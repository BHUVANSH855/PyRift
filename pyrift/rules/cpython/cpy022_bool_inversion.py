"""
CPY022 -- Bitwise inversion on bool deprecated in Python 3.12.

``~True`` and ``~False`` produce ``-2`` and ``-1`` respectively.
Python deprecated bitwise inversion of boolean values in 3.12 and
lists it for removal in 3.16.

This rule intentionally reports only statically provable boolean
constants. It does not infer the type of arbitrary expressions or
variables, avoiding false positives for legitimate integer inversion.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class BoolInversionRule(BaseRule):
    rule_id = "CPY022"
    title = "Bitwise inversion on bool (~True/~False) deprecated in 3.12"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.UnaryOp):
                continue

            if not isinstance(n.op, ast.Invert):
                continue

            operand = n.operand

            # Only report boolean constants. Without type inference,
            # flagging ``~x`` would create false positives for integers
            # and other objects that legitimately implement __invert__.
            if not (
                isinstance(operand, ast.Constant) and isinstance(operand.value, bool)
            ):
                continue

            value = operand.value

            # Do not evaluate ``~value`` here. The operation itself is
            # deprecated on bool in Python 3.12. The historical integer
            # results are deterministic: ~True == -2 and ~False == -1.
            inverted_value = -2 if value else -1
            logical_value = not value

            findings.append(
                Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"Bitwise inversion of bool (~{value}) produces "
                        f"{inverted_value}, not {logical_value}. Bitwise "
                        "inversion of bool has been deprecated since "
                        "Python 3.12 and is scheduled for removal in "
                        "Python 3.16."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        f"Use 'not {value}' for logical negation. "
                        "If you intentionally need the bitwise inversion "
                        "of the underlying integer, use "
                        f"~int({value}) explicitly."
                    ),
                    docs_url=("https://docs.python.org/3/whatsnew/3.12.html"),
                )
            )

        return findings
