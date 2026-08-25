"""
PPY016 — Instance dict ordering not guaranteed on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In CPython 3.7+, instance dictionaries are ordered by insertion.
In PyPy, instance dictionaries use hidden classes (maps) for
performance — if __init__ adds attributes in different orders
across calls, the instance dict order is not guaranteed.

Only flag when __dict__ is accessed outside a class body — i.e.
on external objects. Accessing self.__dict__ inside a method is
a common and generally safe pattern.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


def _is_self_dict(node: ast.Attribute) -> bool:
    """Return True for self.__dict__ or cls.__dict__ patterns."""
    return (
        isinstance(node.value, ast.Name)
        and node.value.id in ("self", "cls", "mcs")
    )


def _inside_class_method(node: ast.AST, parent_map: dict) -> bool:
    """Return True if node is inside a FunctionDef inside a ClassDef."""
    current = parent_map.get(id(node))
    in_func = False
    while current is not None:
        if isinstance(current, ast.FunctionDef):
            in_func = True
        if isinstance(current, ast.ClassDef) and in_func:
            return True
        current = parent_map.get(id(current))
    return False


class InstanceDictOrderRule(BaseRule):
    rule_id = "PPY016"
    title   = "Instance __dict__ ordering not guaranteed on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        # Build parent map for context checking
        parent_map: dict[int, ast.AST] = {}
        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                parent_map[id(child)] = parent

        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Attribute):
                continue
            if n.attr != "__dict__":
                continue
            # Skip self.__dict__ / cls.__dict__ inside class methods
            if _is_self_dict(n) and _inside_class_method(n, parent_map):
                continue
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "Accessing __dict__ on an instance. In CPython 3.7+, "
                    "instance dictionaries are insertion-ordered. In PyPy, "
                    "instance dicts use hidden classes for performance — "
                    "if __init__ adds attributes in different orders across "
                    "calls, dict order is not guaranteed to match CPython's."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.PYPY,
                suggestion=(
                    "Do not rely on instance __dict__ ordering. "
                    "If you need ordered attributes, define them explicitly "
                    "in __init__ in a consistent order, or use "
                    "__slots__ to make the layout fixed."
                ),
                docs_url=(
                    "https://doc.pypy.org/en/latest/cpython_differences.html"
                    "#order-of-dictionary-keys-in-instance-dicts"
                ),
            ))

        return findings