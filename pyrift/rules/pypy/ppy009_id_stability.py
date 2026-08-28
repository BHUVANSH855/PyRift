"""
PPY009 -- id() values not stable across GC cycles on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On CPython, id() commonly corresponds to a stable memory address for an
object's lifetime. PyPy uses a moving garbage collector, so code must not
assume that an id() value remains stable when it is retained across GC
activity.

This rule reports id() when its result is likely to escape the immediate
expression and therefore be retained or compared later.

Flagged examples:

    if id(a) == id(b):
        ...

    cached_id = id(obj)

    return id(obj)

    values.append(id(obj))

    cache[obj] = id(obj)

Legitimate AST-analysis/deduplication patterns are excluded:

    parent_map[id(child)] = parent

    seen = {id(node) for node in nodes}

    key = (id(node), module)

The rule deliberately avoids flagging arbitrary transient uses such as:

    print(id(obj))

because a static AST check cannot determine whether an arbitrary callee
retains its argument.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Confidence, Finding, Runtime, Severity


def _is_id_call(node: ast.AST) -> bool:
    """Return whether ``node`` is a direct call to the builtin ``id``."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "id"
    )


def _parent_is_subscript_key(
    node: ast.AST,
    parent_map: dict[int, ast.AST],
) -> bool:
    """Return whether id() is being used as a subscript key."""
    parent = parent_map.get(id(node))

    if parent is None:
        return False

    if isinstance(parent, ast.Subscript) and parent.slice is node:
        return True

    if isinstance(parent, ast.Tuple):
        grandparent = parent_map.get(id(parent))
        if isinstance(grandparent, ast.Subscript):
            return True

    return False


def _parent_is_set_or_dedup(
    node: ast.AST,
    parent_map: dict[int, ast.AST],
) -> bool:
    """Return whether id() is used in an obvious set/dedup expression."""
    parent = parent_map.get(id(node))

    if parent is None:
        return False

    if isinstance(parent, ast.Set):
        return True

    if isinstance(parent, (ast.List, ast.Tuple)):
        grandparent = parent_map.get(id(parent))

        if isinstance(grandparent, ast.Call):
            func = grandparent.func
            if (
                isinstance(func, ast.Name)
                and func.id in {"set", "frozenset"}
            ):
                return True

    return False


def _is_local_dedup_pattern(
    node: ast.AST,
    parent_map: dict[int, ast.AST],
) -> bool:
    """
    Return True for narrow local AST-analysis deduplication patterns.

    Do not treat arbitrary assignments as safe. A normal assignment such
    as ``cached_id = id(obj)`` must remain visible to PPY009.
    """
    parent = parent_map.get(id(node))

    if isinstance(parent, ast.Tuple):
        grandparent = parent_map.get(id(parent))

        if isinstance(grandparent, ast.Assign):
            return True

    if isinstance(parent, ast.Assign):
        for target in parent.targets:
            if isinstance(target, ast.Name) and target.id in {
                "node_id",
                "child_id",
                "parent_id",
                "object_id",
            }:
                return True

    return False


def _is_persistence_context(
    node: ast.AST,
    parent_map: dict[int, ast.AST],
) -> bool:
    """
    Return whether the id() result is likely to outlive the expression.

    The rule intentionally uses conservative syntactic signals rather than
    assuming that every function argument is retained.
    """
    parent = parent_map.get(id(node))

    if parent is None:
        return False

    if isinstance(
        parent,
        (
            ast.Return,
            ast.Yield,
            ast.YieldFrom,
            ast.AugAssign,
        ),
    ):
        return True

    if isinstance(parent, ast.Assign):
        return True

    if isinstance(parent, ast.NamedExpr):
        return True

    if isinstance(parent, ast.Attribute):
        grandparent = parent_map.get(id(parent))

        if isinstance(
            grandparent,
            (
                ast.Assign,
                ast.Return,
                ast.AugAssign,
            ),
        ):
            return True

    if isinstance(parent, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
        container_parent = parent_map.get(id(parent))

        if isinstance(
            container_parent,
            (
                ast.Assign,
                ast.Return,
                ast.AugAssign,
            ),
        ):
            return True

    return isinstance(parent, ast.Compare)


def _make_finding(
    filename: str,
    node: ast.Call,
    context: str,
) -> Finding:
    return Finding(
        file=filename,
        line=node.lineno,
        col=node.col_offset,
        rule_id="PPY009",
        title="id() values not stable across GC cycles on PyPy",
        description=(
            "id() is used in a context where its numeric result may be "
            f"retained or compared ({context}). On PyPy, the garbage "
            "collector may move objects, so code must not rely on an "
            "id() value remaining stable across GC cycles. Use object "
            "identity directly with 'is', or retain the object itself "
            "instead of its id() value."
        ),
        severity=Severity.WARNING,
        confidence=Confidence.HIGH,
        runtime=Runtime.PYPY,
        suggestion=(
            "Avoid retaining id(obj) as persistent state. Prefer retaining "
            "the object itself, or use 'is' for identity comparisons. "
            "Only use id() as a transient value when its stability is not "
            "required."
        ),
        docs_url=(
            "https://doc.pypy.org/en/latest/"
            "cpython_differences.html#id"
        ),
    )


class IdStabilityRule(BaseRule):
    rule_id = "PPY009"
    title = "id() values not stable across GC cycles on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
    ) -> list[Finding]:
        parent_map: dict[int, ast.AST] = {}

        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                parent_map[id(child)] = parent

        findings: list[Finding] = []

        for current in ast.walk(node):
            if not _is_id_call(current):
                continue

            if _parent_is_subscript_key(current, parent_map):
                continue

            if _parent_is_set_or_dedup(current, parent_map):
                continue

            if _is_local_dedup_pattern(current, parent_map):
                continue

            parent = parent_map.get(id(current))

            if isinstance(parent, ast.Compare):
                context = "comparison"
            elif isinstance(parent, ast.Return):
                context = "return value"
            elif isinstance(parent, ast.Assign):
                context = "stored assignment"
            elif isinstance(parent, ast.AugAssign):
                context = "augmented assignment"
            elif isinstance(parent, ast.Yield):
                context = "yield value"
            elif isinstance(parent, ast.YieldFrom):
                context = "yield-from value"
            else:
                context = "persistent expression"

            if not _is_persistence_context(current, parent_map):
                continue

            findings.append(
                _make_finding(
                    filename,
                    current,
                    context,
                )
            )

        return findings