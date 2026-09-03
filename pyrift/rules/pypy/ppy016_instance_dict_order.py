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
from pyrift.targets import TargetConfig

_ORDERED_METHODS = {"keys", "values", "items"}
_ORDER_SENSITIVE_BUILTINS = {
    "list",
    "tuple",
    "iter",
    "reversed",
    "dict",
}


def _is_sorted_call(node: ast.AST) -> bool:
    """Return whether *node* is a direct sorted(...) call."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "sorted"
    )


def _is_order_sensitive(
    node: ast.Attribute,
    parent_map: dict[int, ast.AST],
) -> bool:
    """
    Determine whether an instance __dict__ is used in an
    order-sensitive context.

    Important cases:

        list(obj.__dict__)              -> report
        tuple(obj.__dict__)             -> report
        iter(obj.__dict__)              -> report
        reversed(obj.__dict__)          -> report
        dict(obj.__dict__)              -> report

        sorted(obj.__dict__)            -> don't report
        sorted(obj.__dict__.items())    -> don't report

        obj.__dict__.keys()             -> report
        obj.__dict__.values()           -> report
        obj.__dict__.items()            -> report

        for x in obj.__dict__:          -> report
        [x for x in obj.__dict__]:      -> report
    """
    current = parent_map.get(id(node))

    if current is None:
        return False

    # Direct iteration:
    #
    #     for key in obj.__dict__:
    #
    if isinstance(current, ast.For):
        return current.iter is node

    # Comprehension iteration:
    #
    #     [key for key in obj.__dict__]
    #
    if isinstance(current, ast.comprehension):
        return current.iter is node

    # Direct calls operating on obj.__dict__.
    if isinstance(current, ast.Call):
        if not isinstance(current.func, ast.Name):
            return False

        # sorted() establishes a deterministic order, so the original
        # dictionary iteration order is not part of the resulting order.
        if current.func.id == "sorted":
            return False

        return current.func.id in _ORDER_SENSITIVE_BUILTINS

    # Handle:
    #
    #     obj.__dict__.keys()
    #     obj.__dict__.values()
    #     obj.__dict__.items()
    #
    # The Attribute node is the receiver of the method call.
    if isinstance(current, ast.Attribute):
        if current.attr not in _ORDERED_METHODS:
            return False

        call = parent_map.get(id(current))

        if not (
            isinstance(call, ast.Call)
            and call.func is current
        ):
            return False

        # If this method call is itself consumed by sorted(), then the
        # final result has an explicitly established ordering.
        grandparent = parent_map.get(id(call))
        return not _is_sorted_call(grandparent)

    return False


class InstanceDictOrderRule(BaseRule):
    rule_id = "PPY016"
    title = "Instance __dict__ order-sensitive access may differ on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
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

            if not _is_order_sensitive(current, parent_map):
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