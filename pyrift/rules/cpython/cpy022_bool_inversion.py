"""
CPY022 — Bitwise inversion on bool deprecated in Python 3.12
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~True and ~False produce -2 and -1 respectively — surprising and
unintuitive. This behaviour is deprecated since Python 3.12 and
will produce a DeprecationWarning. Use 'not x' for logical negation.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class BoolInversionRule(BaseRule):
    rule_id = "CPY022"
    title   = "Bitwise inversion on bool (~True/~False) deprecated in 3.12"
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

            if not (
                isinstance(operand, ast.Constant)
                and isinstance(operand.value, bool)
            ):
                continue

            value = operand.value

            # Avoid evaluating ``~value`` directly here because Python
            # 3.16 deprecates bitwise inversion of bool and emits a
            # DeprecationWarning. The integer results are deterministic:
            # ~True == -2 and ~False == -1.
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
                        f"Bitwise inversion of bool (~{value}) "
                        f"produces {inverted_value}, not {logical_value}. "
                        "This is deprecated since Python 3.12 and raises "
                        "DeprecationWarning. It will be removed in a "
                        "future version."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        f"Use 'not {value}' for logical negation. "
                        "If you need the bitwise integer result, use "
                        f"~int({value}) explicitly."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.12.html"
                    ),
                )
            )

        return findings
