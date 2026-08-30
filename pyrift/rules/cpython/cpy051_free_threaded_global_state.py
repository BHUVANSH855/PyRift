"""
CPY051 — Unsynchronized mutation of module-level mutable state
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Flag module-level mutable state when runtime code mutates that state
without recognizable synchronization.

Merely constructing a list/dict/set at module scope is not inherently
unsafe: module initialization happens before normal runtime concurrency
begins.

The compatibility risk is code that relies on implicit GIL protection
for shared mutable state accessed or mutated from functions or methods.

Mutations performed while protected by a recognizable lock or
synchronization context are not reported.

Conservative scope: this is a *heuristic*, not proof of a data race.
A lock is only recognized from a small, hand-picked set of synchronization
objects (threading.Lock/RLock/Condition/Semaphore/Event/Barrier and
asyncio.Lock) used through a ``with`` block or acquire/release. Any other
synchronization primitive, user lock wrapper, or lock used indirectly is
treated as unprotected, which may under-report. The rule also does not
attempt flow-sensitive data-race analysis: two functions touching the
same name are considered independently. Severity is WARNING because a
static check cannot prove the code is actually run concurrently.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_MUTATING_METHODS = {
    "append", "clear", "extend", "insert", "pop", "remove",
    "reverse", "sort", "update", "setdefault", "add", "discard",
    "difference_update", "intersection_update",
    "symmetric_difference_update", "union_update",
}

_LOCK_TYPES = {
    "Lock", "RLock", "Condition", "Semaphore",
    "BoundedSemaphore", "Event", "Barrier",
}


# ── AST helpers ────────────────────────────────────────────────────────────

def _root_name(expr: ast.AST) -> str | None:
    """Return the root Name for expressions like ``cache`` or ``cache[0]``."""
    while isinstance(expr, (ast.Subscript, ast.Attribute)):
        expr = expr.value
    return expr.id if isinstance(expr, ast.Name) else None


def _attribute_path(expr: ast.AST) -> tuple[str, ...]:
    """Return an attribute path such as ``('self', '_lock')``."""
    parts: list[str] = []
    while isinstance(expr, ast.Attribute):
        parts.append(expr.attr)
        expr = expr.value
    if isinstance(expr, ast.Name):
        parts.append(expr.id)
        return tuple(reversed(parts))
    return ()


def _is_lock_constructor(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id in _LOCK_TYPES
    if isinstance(func, ast.Attribute):
        return func.attr in _LOCK_TYPES
    return False


def _is_lock_expression(expr: ast.AST) -> bool:
    if isinstance(expr, ast.Call):
        return _is_lock_constructor(expr)
    if isinstance(expr, (ast.Name, ast.Attribute)):
        return bool(_attribute_path(expr))
    return False


def _lock_key(expr: ast.AST) -> tuple[str, ...] | None:
    if isinstance(expr, ast.Call):
        return ("__tmp__",) if _is_lock_constructor(expr) else None
    if isinstance(expr, (ast.Name, ast.Attribute)):
        path = _attribute_path(expr)
        return path or None
    return None


# ── Mutation detection ─────────────────────────────────────────────────────

def _mutation_name(node: ast.AST) -> str | None:
    """Return the module-level name mutated by *node*, if any."""
    if isinstance(node, ast.AugAssign):
        return _root_name(node.target)
    if isinstance(node, ast.Delete):
        for target in node.targets:
            name = _root_name(target)
            if name is not None:
                return name
        return None
    if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store):
        return _root_name(node.value)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _MUTATING_METHODS
    ):
        return _root_name(node.func.value)
    return None


# ── Lock-aware traversal ───────────────────────────────────────────────────

def _walk_with(
    statement: ast.With | ast.AsyncWith,
    protected: set[tuple[str, ...]],
    walk_fn,
) -> None:
    """Walk a ``with`` block while holding its recognized locks."""
    nested = set(protected)
    for item in statement.items:
        key = _lock_key(item.context_expr)
        if key is not None and _is_lock_expression(item.context_expr):
            nested.add(key)
        if item.optional_vars is not None:
            opt = _lock_key(item.optional_vars)
            if opt is not None:
                nested.add(opt)
    for child in statement.body:
        walk_fn(child, nested)


def _walk_try(
    statement: ast.Try,
    protected: set[tuple[str, ...]],
    walk_fn,
    walk_block_fn,
) -> None:
    """Walk a try statement preserving lock state through all clauses."""
    walk_block_fn(statement.body, protected)
    for handler in statement.handlers:
        walk_block_fn(handler.body, protected)
    walk_block_fn(statement.orelse, protected)
    walk_block_fn(statement.finalbody, protected)


def _walk_block(
    statements: list[ast.stmt],
    protected: set[tuple[str, ...]],
    walk_fn,
) -> None:
    """Walk statements in execution order."""
    for stmt in statements:
        walk_fn(stmt, protected)


# ── Module-level state collector ───────────────────────────────────────────

def _collect_module_mutable(
    module: ast.Module,
) -> tuple[set[str], dict[str, ast.stmt]]:
    """Return mutable names and their assignment nodes from module body."""
    mutable: set[str] = set()
    assignments: dict[str, ast.stmt] = {}
    for stmt in module.body:
        if not isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            continue
        if not isinstance(stmt.value, (ast.List, ast.Dict, ast.Set)):
            continue
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        for target in targets:
            if isinstance(target, ast.Name):
                mutable.add(target.id)
                assignments[target.id] = stmt
    return mutable, assignments


# ── Function inspector ─────────────────────────────────────────────────────

def _inspect_function(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    mutable_names: set[str],
    unsynchronized: set[str],
) -> None:
    """Inspect a function for unsynchronized mutations of module-level state."""
    nested_functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    def walk(node: ast.AST, protected: set[tuple[str, ...]]) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not function:
            if node not in nested_functions:
                nested_functions.append(node)
            return
        if isinstance(node, ast.Lambda):
            return
        if isinstance(node, (ast.With, ast.AsyncWith)):
            _walk_with(node, protected, walk)
            return
        if isinstance(node, ast.Try):
            _walk_try(node, protected, walk,
                      lambda stmts, p: _walk_block(stmts, p, walk))
            return
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute):
                key = _lock_key(call.func.value)
                if key is not None:
                    if call.func.attr == "acquire":
                        protected.add(key)
                        return
                    if call.func.attr == "release":
                        protected.discard(key)
                        return

        name = _mutation_name(node)
        if name in mutable_names and not protected:
            unsynchronized.add(name)
        if name is not None:
            return
        for child in ast.iter_child_nodes(node):
            walk(child, protected)

    walk(function, set())
    for nested in nested_functions:
        _inspect_function(nested, mutable_names, unsynchronized)


def _discover_functions(
    body: list[ast.stmt],
    mutable_names: set[str],
    unsynchronized: set[str],
) -> None:
    """Discover all runtime functions in the module body."""
    for stmt in body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _inspect_function(stmt, mutable_names, unsynchronized)
        elif isinstance(stmt, ast.ClassDef):
            _discover_functions(stmt.body, mutable_names, unsynchronized)
        else:
            for child in ast.iter_child_nodes(stmt):
                if isinstance(child, ast.stmt):
                    _discover_functions([child], mutable_names, unsynchronized)


# ── Rule ───────────────────────────────────────────────────────────────────

class FreeThreadedGlobalStateRule(BaseRule):
    rule_id = "CPY051"
    title = (
        "Module-level mutable state may require synchronization "
        "in free-threaded Python"
    )
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        if not isinstance(node, ast.Module):
            return []

        mutable_names, assignments = _collect_module_mutable(node)
        if not mutable_names:
            return []

        unsynchronized: set[str] = set()
        _discover_functions(node.body, mutable_names, unsynchronized)

        return [
            Finding(
                file=filename,
                line=assignments[name].lineno,
                col=assignments[name].col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"Module-level mutable variable '{name}' is mutated "
                    "from runtime function code without recognizable "
                    "synchronization. In a CPython free-threaded build, "
                    "concurrent access to shared mutable state may require "
                    "explicit synchronization."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.13",
                suggestion=(
                    "If this state is shared across threads, protect "
                    "compound mutations and read-modify-write sequences "
                    "with a lock, or use an appropriate thread-safe "
                    "abstraction."
                ),
                docs_url=(
                    "https://docs.python.org/3/howto/"
                    "free-threading-python.html"
                ),
            )
            for name in sorted(unsynchronized)
        ]