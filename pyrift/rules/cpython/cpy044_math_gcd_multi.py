"""
CPY044 — math.gcd() with multiple arguments requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In Python 3.5-3.8, math.gcd() only accepts exactly two arguments.
In Python 3.9+, math.gcd() accepts multiple arguments (zero or more).
Calling math.gcd(a, b, c) on Python 3.8 raises TypeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class MathGcdMultiRule(BaseRule):
    rule_id = "CPY044"
    title   = "math.gcd() with multiple args requires Python 3.9+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "gcd"
                and isinstance(func.value, ast.Name)
                and func.value.id == "math"
                and len(n.args) > 2
            ):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"math.gcd() is called with {len(n.args)} arguments. "
                            "In Python 3.8 and below, math.gcd() only accepts "
                            "exactly 2 arguments. The multi-argument form was "
                            "added in Python 3.9. This raises TypeError on 3.8."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.0",
                        affected_until="3.8",
                        suggestion=(
                            "For Python 3.8 compatibility, chain math.gcd calls: "
                            "from functools import reduce; "
                            "reduce(math.gcd, [a, b, c])"
                        ),
                        docs_url=(
                            "https://docs.python.org/3/library/math.html#math.gcd"
                        ),
                    ))
        return findings