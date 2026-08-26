"""
PPY016 — Instance dict ordering not guaranteed on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Only report instance __dict__ usage when the code structurally depends
on iteration/order.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


def _is_self_dict(node: ast.Attribute) -> bool:
    return (
        isinstance(node.value, ast.Name)
        and node.value.id in {"self", "cls", "mcs"}
    )


def _inside_class_method(
    node: ast.AST,
    parent_map: dict[int, ast.AST],
) -> bool:
    current = parent_map.get(id(node))
    in_func = False

    while current is not None:
        if isinstance(
            current,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            in_func = True

        if isinstance(current, ast.ClassDef) and in_func:
            return True

        current = parent_map.get(id(current))

    return False


def _is_order_sensitive(
    node: ast.Attribute,
    parent_map: dict[int, ast.AST],
) -> bool:
    current = parent_map.get(id(node))

    if current is None:
        return False

    if isinstance(current, ast.For):
        return current.iter is node

    if isinstance(current, ast.comprehension):
        return current.iter is node

    if isinstance(current, ast.Call):
        if isinstance(current.func, ast.Name):
            return current.func.id in {
                "list",
                "tuple",
                "iter",
                "sorted",
                "reversed",
            }

        return False

    return isinstance(current, ast.Subscript)


class InstanceDictOrderRule(BaseRule):
    rule_id = "PPY016"
    title = "Instance __dict__ order-sensitive access may differ on PyPy"
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
            if not isinstance(current, ast.Attribute):
                continue

            if current.attr != "__dict__":
                continue

            if (
                _is_self_dict(current)
                and _inside_class_method(
                    current,
                    parent_map,
                )
            ):
                continue

            if not _is_order_sensitive(
                current,
                parent_map,
            ):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=current.lineno,
                    col=current.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The code uses an instance __dict__ in an "
                        "order-sensitive context. CPython preserves "
                        "instance dictionary insertion order, while "
                        "PyPy does not provide the same ordering "
                        "guarantee for this usage."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Do not depend on instance __dict__ iteration "
                        "order. Use an explicitly ordered data structure "
                        "when ordering is part of the program's contract."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                        "#order-of-dictionary-keys-in-instance-dicts"
                    ),
                )
            )

        return findings