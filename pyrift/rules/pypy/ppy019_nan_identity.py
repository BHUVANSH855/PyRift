"""
PPY019 — float('nan') identity differs between CPython and PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, float('nan') is float('nan') is False — each call
creates a new object. On PyPy, there is only one object per bit
pattern — float('nan') is float('nan') is True. This means sets
cannot contain multiple NaN values on PyPy, but can on CPython.

The finding is raised at the ``is``/``is not`` comparison node where
the identity of a float('nan') value is tested, not at the creation
site. This avoids false positives on helper functions that create
NaN objects legitimately (e.g. for assignment), without an identity
comparison.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


def _is_float_nan(node: ast.AST) -> bool:
    """Return True when *node* is a float('nan') / float('NaN') / … call."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not (isinstance(func, ast.Name) and func.id == "float"):
        return False
    if not node.args:
        return False
    arg = node.args[0]
    return (
        isinstance(arg, ast.Constant)
        and isinstance(arg.value, str)
        and arg.value.lower() in ("nan", "+nan", "-nan")
    )


class NanIdentityRule(BaseRule):
    rule_id = "PPY019"
    title   = "float('nan') identity differs between CPython and PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Fire at the ``is``/``is not`` comparison, not at the creation site.
            if not isinstance(n, ast.Compare):
                continue
            # ast.Compare: left op[0] comparators[0] op[1] comparators[1] …
            operands = [n.left, *n.comparators]
            ops = n.ops
            for op, left, right in zip(ops, operands, operands[1:]):
                if not isinstance(op, (ast.Is, ast.IsNot)):
                    continue
                if _is_float_nan(left) or _is_float_nan(right):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "float('nan') creates a new object each time on "
                            "CPython — so float('nan') is float('nan') is False "
                            "and a set can contain multiple NaN values. "
                            "On PyPy, there is only one NaN object per bit pattern "
                            "— float('nan') is float('nan') is True, and a set "
                            "cannot contain multiple NaN values. This causes "
                            "silent behaviour differences in set operations."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Use math.isnan() to check for NaN rather than "
                            "identity comparisons. Do not rely on multiple NaN "
                            "values in a set — use filtering instead."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                            "#object-identity-of-primitive-values-is-and-id"
                        ),
                    ))
                    break  # one finding per Compare node is enough

        return findings