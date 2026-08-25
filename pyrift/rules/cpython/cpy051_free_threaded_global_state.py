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
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

_MUTATING_METHODS = {
    "append",
    "clear",
    "extend",
    "insert",
    "pop",
    "remove",
    "reverse",
    "sort",
    "update",
    "setdefault",
    "add",
    "discard",
    "difference_update",
    "intersection_update",
    "symmetric_difference_update",
    "union_update",
}


_LOCK_TYPES = {
    "Lock",
    "RLock",
    "Condition",
    "Semaphore",
    "BoundedSemaphore",
    "Event",
    "Barrier",
}


def _root_name(expr: ast.AST) -> str | None:
    """Return the root name for expressions such as ``cache`` or ``cache[0]``."""
    while isinstance(expr, (ast.Subscript, ast.Attribute)):
        expr = expr.value

    return expr.id if isinstance(expr, ast.Name) else None


def _attribute_path(expr: ast.AST) -> tuple[str, ...]:
    """Return an attribute path such as ``self._lock``."""
    parts: list[str] = []

    while isinstance(expr, ast.Attribute):
        parts.append(expr.attr)
        expr = expr.value

    if isinstance(expr, ast.Name):
        parts.append(expr.id)
        return tuple(reversed(parts))

    return ()


def _is_lock_constructor(call: ast.Call) -> bool:
    """Return whether *call* constructs a recognizable synchronization object."""
    func = call.func

    if isinstance(func, ast.Name):
        return func.id in _LOCK_TYPES

    if isinstance(func, ast.Attribute):
        return func.attr in _LOCK_TYPES

    return False


def _is_lock_expression(expr: ast.AST) -> bool:
    """
    Return whether *expr* looks like a recognizable lock expression.

    Examples accepted:

    ``lock``
    ``self._lock``
    ``module.lock``
    ``threading.Lock()``
    ``threading.RLock()``
    """
    if isinstance(expr, ast.Call):
        return _is_lock_constructor(expr)

    if isinstance(expr, (ast.Name, ast.Attribute)):
        return bool(_attribute_path(expr))

    return False


def _lock_key(expr: ast.AST) -> tuple[str, ...] | None:
    """Return a stable key for a lock expression."""
    if isinstance(expr, ast.Call):
        if _is_lock_constructor(expr):
            return ("<temporary-lock>",)

        return None

    if isinstance(expr, (ast.Name, ast.Attribute)):
        path = _attribute_path(expr)
        return path or None

    return None


class FreeThreadedGlobalStateRule(BaseRule):
    rule_id = "CPY051"
    title = (
        "Unsynchronized module-level mutable state may be unsafe "
        "in free-threaded Python"
    )
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        if not isinstance(node, ast.Module):
            return []

        mutable_names: set[str] = set()
        assignments: dict[str, ast.stmt] = {}

        # Only collect mutable objects created at module scope.
        for stmt in node.body:
            if not isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                continue

            value = stmt.value

            if not isinstance(value, (ast.List, ast.Dict, ast.Set)):
                continue

            if isinstance(stmt, ast.Assign):
                targets = stmt.targets
            else:
                targets = [stmt.target]

            for target in targets:
                if isinstance(target, ast.Name):
                    mutable_names.add(target.id)
                    assignments[target.id] = stmt

        if not mutable_names:
            return []

        unsynchronized_mutations: set[str] = set()

        def mutation_name(current: ast.AST) -> str | None:
            """Return the module-level mutable name mutated by *current*."""
            if isinstance(current, ast.AugAssign):
                return _root_name(current.target)

            if isinstance(current, ast.Delete):
                for target in current.targets:
                    name = _root_name(target)
                    if name is not None:
                        return name

                return None

            if isinstance(current, ast.Subscript):
                if isinstance(current.ctx, ast.Store):
                    return _root_name(current.value)

                return None

            if (
                isinstance(current, ast.Call)
                and isinstance(current.func, ast.Attribute)
                and current.func.attr in _MUTATING_METHODS
            ):
                return _root_name(current.func.value)

            return None

        def inspect_mutation(
            current: ast.AST,
            protected_locks: set[tuple[str, ...]],
        ) -> None:
            """
            Inspect one AST node for a mutation.

            This helper intentionally does not recurse. The caller controls
            traversal so that lock state follows execution order.
            """
            name = mutation_name(current)

            if name in mutable_names and not protected_locks:
                unsynchronized_mutations.add(name)

        def inspect_with(
            statement: ast.With,
            protected_locks: set[tuple[str, ...]],
            walk,
        ) -> None:
            """Walk a ``with`` block while holding its recognized locks."""
            nested_locks = set(protected_locks)

            for item in statement.items:
                lock_key = _lock_key(item.context_expr)

                if (
                    lock_key is not None
                    and _is_lock_expression(item.context_expr)
                ):
                    nested_locks.add(lock_key)

                if item.optional_vars is not None:
                    optional_lock = _lock_key(item.optional_vars)

                    if optional_lock is not None:
                        nested_locks.add(optional_lock)

            for child in statement.body:
                walk(child, nested_locks)

        def inspect_try(
            statement: ast.Try,
            protected_locks: set[tuple[str, ...]],
            walk,
        ) -> None:
            """
            Walk a try statement while preserving lock state.

            In particular, mutations performed in ``finally`` can release a
            lock. That release must affect statements following the try.
            """
            walk_block(statement.body, protected_locks, walk)

            for handler in statement.handlers:
                walk_block(handler.body, protected_locks, walk)

            walk_block(statement.orelse, protected_locks, walk)

            # The finally block executes after the try/except portion and can
            # change synchronization state for code following the try.
            walk_block(statement.finalbody, protected_locks, walk)

        def walk_block(
            statements: list[ast.stmt],
            protected_locks: set[tuple[str, ...]],
            walk,
        ) -> None:
            """
            Walk statements in execution order.

            ``protected_locks`` is intentionally mutated in place so that an
            acquire/release pair changes the state seen by later statements.
            """
            for statement in statements:
                walk(statement, protected_locks)

        def inspect_function(
            function: ast.FunctionDef | ast.AsyncFunctionDef,
        ) -> None:
            nested_functions: list[
                ast.FunctionDef | ast.AsyncFunctionDef
            ] = []

            def collect_nested_functions(current: ast.AST) -> None:
                """
                Collect nested runtime functions without treating their bodies
                as part of the enclosing function's execution.
                """
                if isinstance(
                    current,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                ):
                    if current is not function:
                        nested_functions.append(current)

                    return

                if isinstance(current, ast.Lambda):
                    return

                for child in ast.iter_child_nodes(current):
                    collect_nested_functions(child)

            def walk(
                current: ast.AST,
                protected_locks: set[tuple[str, ...]],
            ) -> None:
                # Nested functions have their own runtime execution scope.
                # Collect them separately instead of walking their bodies as
                # though they execute when the outer function executes.
                if (
                    isinstance(
                        current,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    )
                    and current is not function
                ):
                    if current not in nested_functions:
                        nested_functions.append(current)

                    return

                if isinstance(current, ast.Lambda):
                    return

                if isinstance(current, ast.With):
                    inspect_with(current, protected_locks, walk)
                    return

                if isinstance(current, ast.AsyncWith):
                    inspect_with(current, protected_locks, walk)
                    return

                if isinstance(current, ast.Try):
                    inspect_try(current, protected_locks, walk)
                    return

                if isinstance(current, ast.Expr):
                    call = current.value

                    if (
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                    ):
                        lock_key = _lock_key(call.func.value)

                        if (
                            lock_key is not None
                            and call.func.attr == "acquire"
                        ):
                            protected_locks.add(lock_key)
                            return

                        if (
                            lock_key is not None
                            and call.func.attr == "release"
                        ):
                            protected_locks.discard(lock_key)
                            return

                inspect_mutation(current, protected_locks)

                # A mutation node is fully handled above. Do not descend into
                # its children and accidentally inspect the same operation
                # again.
                if mutation_name(current) is not None:
                    return

                for child in ast.iter_child_nodes(current):
                    walk(child, protected_locks)

            # Start with an independent lock state for this function.
            walk(function, set())

            # Analyze nested functions separately. Their lock state starts
            # fresh because they execute independently of the enclosing
            # function's current control-flow state.
            for nested_function in nested_functions:
                inspect_function(nested_function)

        # Discover every runtime function, including functions nested inside
        # other functions and methods nested inside classes.
        def discover_functions(body: list[ast.stmt]) -> None:
            for statement in body:
                if isinstance(
                    statement,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                ):
                    inspect_function(statement)
                    continue

                if isinstance(statement, ast.ClassDef):
                    discover_functions(statement.body)

                    for child in statement.body:
                        if isinstance(
                            child,
                            (ast.FunctionDef, ast.AsyncFunctionDef),
                        ):
                            inspect_function(child)

                    continue

                for child in ast.iter_child_nodes(statement):
                    if isinstance(child, ast.stmt):
                        discover_functions([child])

        discover_functions(node.body)

        findings: list[Finding] = []

        for name in sorted(unsynchronized_mutations):
            stmt = assignments[name]

            findings.append(
                Finding(
                    file=filename,
                    line=stmt.lineno,
                    col=stmt.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"Module-level mutable variable '{name}' is mutated "
                        "from runtime function code without recognizable "
                        "synchronization. In a CPython free-threaded build, "
                        "code that relies on the GIL to coordinate compound "
                        "or unsynchronized access to shared state can "
                        "behave differently."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "If this state is shared across threads, protect "
                        "compound mutations and read-modify-write sequences "
                        "with a lock, or use an appropriate thread-safe "
                        "abstraction. Individual built-in list/dict/set "
                        "operations should not be treated as a blanket "
                        "guarantee of thread safety."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/howto/"
                        "free-threading-python.html"
                    ),
                )
            )

        return findings