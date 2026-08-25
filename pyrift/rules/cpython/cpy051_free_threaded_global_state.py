"""
CPY051 — Unsynchronized mutation of module-level mutable state
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Flag module-level mutable state when the same module also mutates that
state. Merely defining a list/dict/set at module scope is not inherently
unsafe: the free-threaded CPython build still provides internal safety for
individual built-in operations. The compatibility risk is code that relies
on implicit GIL protection for a sequence of mutations or other shared
state coordination.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

_MUTATING_METHODS = {
    "append", "clear", "extend", "insert", "pop", "remove", "reverse",
    "sort", "update", "setdefault", "add", "discard", "difference_update",
    "intersection_update", "symmetric_difference_update", "union_update",
}


def _root_name(expr: ast.AST) -> str | None:
    """Return the root name for expressions such as ``cache`` or ``cache[0]``."""
    while isinstance(expr, (ast.Subscript, ast.Attribute)):
        expr = expr.value
    return expr.id if isinstance(expr, ast.Name) else None


class FreeThreadedGlobalStateRule(BaseRule):
    rule_id = "CPY051"
    title = "Unsynchronized module-level mutable state may be unsafe in free-threaded Python"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        if not isinstance(node, ast.Module):
            return []

        mutable_names: set[str] = set()
        assignments: dict[str, ast.stmt] = {}

        for stmt in node.body:
            if not isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                continue

            value = stmt.value
            if not isinstance(value, (ast.List, ast.Dict, ast.Set)):
                continue

            targets: list[ast.expr] = []
            if isinstance(stmt, ast.Assign):
                targets = list(stmt.targets)
            elif isinstance(stmt, ast.AnnAssign):
                targets = [stmt.target]

            for target in targets:
                if isinstance(target, ast.Name):
                    mutable_names.add(target.id)
                    assignments[target.id] = stmt

        if not mutable_names:
            return []

        mutated: set[str] = set()
        for current in ast.walk(node):
            if isinstance(current, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                # A plain reassignment is not enough to establish mutation of
                # the original object; inspect subscripts/augassign/methods.
                continue

            if isinstance(current, (ast.AugAssign, ast.Delete)):
                name = _root_name(current.target)
                if name in mutable_names:
                    mutated.add(name)
                continue

            if isinstance(current, ast.Subscript):
                if isinstance(current.ctx, ast.Store):
                    name = _root_name(current.value)
                    if name in mutable_names:
                        mutated.add(name)
                continue

            if isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
                name = _root_name(current.func.value)
                if name in mutable_names and current.func.attr in _MUTATING_METHODS:
                    mutated.add(name)

        findings: list[Finding] = []
        for name in sorted(mutated):
            stmt = assignments[name]
            findings.append(Finding(
                file=filename,
                line=stmt.lineno,
                col=stmt.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"Module-level mutable variable '{name}' is mutated in "
                    "this module. In a CPython free-threaded build, code that "
                    "relies on the GIL to coordinate compound or unsynchronized "
                    "access to shared state can behave differently."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.13",
                suggestion=(
                    "If this state is shared across threads, protect compound "
                    "mutations and read-modify-write sequences with a lock, or "
                    "use an appropriate thread-safe abstraction. Individual "
                    "built-in list/dict/set operations should not be treated "
                    "as a blanket guarantee of thread safety."
                ),
                docs_url="https://docs.python.org/3/howto/free-threading-python.html",
            ))

        return findings
