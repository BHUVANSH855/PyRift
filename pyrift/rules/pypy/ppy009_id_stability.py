"""
PPY009 -- id() values not stable across GC cycles on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, id() returns a stable memory address for an object's
lifetime. On PyPy, the GC may move objects in memory, so id() can
return different values for the same object across GC cycles.

Only flag when id() result is used in a context where stability
matters — comparisons, set membership, or stored in a variable.

NOT flagged:
  - id(x) used as a dict key (parent_map[id(x)] = parent)
  - id(x) used directly in a set for deduplication
  - transient use as a tuple element for local dedup
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Confidence, Finding, Runtime, Severity


def _is_id_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "id"
    )


def _parent_is_subscript_key(node: ast.AST,
                              parent_map: dict[int, ast.AST]) -> bool:
    """True if id() is used as a subscript key: d[id(x)]"""
    parent = parent_map.get(id(node))
    if parent is None:
        return False
    # Direct subscript: d[id(x)]
    if isinstance(parent, ast.Subscript) and parent.slice is node:
        return True
    # Tuple in subscript: d[(id(x), y)]
    if isinstance(parent, ast.Tuple):
        grandparent = parent_map.get(id(parent))
        if isinstance(grandparent, ast.Subscript):
            return True
    return False


def _parent_is_set_or_dedup(node: ast.AST,
                             parent_map: dict[int, ast.AST]) -> bool:
    """True if id() is used in a set literal or set() call for dedup."""
    parent = parent_map.get(id(node))
    if parent is None:
        return False
    # set literal: {id(x), id(y)}
    if isinstance(parent, ast.Set):
        return True
    # set() call argument
    if isinstance(parent, (ast.List, ast.Tuple)):
        gp = parent_map.get(id(parent))
        if isinstance(gp, ast.Call):
            func = gp.func
            if isinstance(func, ast.Name) and func.id in ("set", "frozenset"):
                return True
    return False


def _is_local_dedup_pattern(node: ast.AST,
                             parent_map: dict[int, ast.AST]) -> bool:
    """True for: node_id = id(x) or key = (id(x), ...) patterns
    used in local dedup sets — common in AST parent-map building."""
    parent = parent_map.get(id(node))
    # id() inside a tuple that's assigned to a variable
    if isinstance(parent, ast.Tuple):
        gp = parent_map.get(id(parent))
        if isinstance(gp, ast.Assign):
            return True
    # Direct assignment: node_id = id(x)
    return isinstance(parent, ast.Assign)


class IdStabilityRule(BaseRule):
    rule_id = "PPY009"
    title = "id() values not stable across GC cycles on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        # Build parent map
        parent_map: dict[int, ast.AST] = {}
        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                parent_map[id(child)] = parent

        findings: list[Finding] = []

        for n in ast.walk(node):
            if not _is_id_call(n):
                continue

            # Skip legitimate uses: dict key, set dedup, local dedup variable
            if _parent_is_subscript_key(n, parent_map):
                continue
            if _parent_is_set_or_dedup(n, parent_map):
                continue
            if _is_local_dedup_pattern(n, parent_map):
                continue

            # Only flag when id() result is compared or used in a way
            # where stability across GC cycles matters
            parent = parent_map.get(id(n))

            # Flag: if id(x) == id(y) comparisons
            if isinstance(parent, ast.Compare):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "id() is used in a comparison. On CPython, id() "
                        "returns a stable memory address. On PyPy, the GC "
                        "may move objects, so id() values are not stable "
                        "across GC cycles. Use 'is' for identity comparison."
                    ),
                    severity=Severity.WARNING,
                    confidence=Confidence.HIGH,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use 'x is y' instead of 'id(x) == id(y)' for "
                        "identity comparison — works correctly on both "
                        "CPython and PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html#id"
                    ),
                ))

        return findings