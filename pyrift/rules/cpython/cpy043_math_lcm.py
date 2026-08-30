"""
CPY043 — math.lcm() requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
math.lcm() (least common multiple) was added in Python 3.9.
Calling it on Python 3.8 or below raises AttributeError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class MathLcmRule(BaseRule):
    rule_id = "CPY043"
    title   = "math.lcm() requires Python 3.9+"
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
            if (isinstance(func, ast.Attribute) and
                    func.attr == "lcm" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "math"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "math.lcm() was added in Python 3.9. "
                        "Calling it on Python 3.8 or below raises "
                        "AttributeError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.8",
                    suggestion=(
                        "For Python 3.8 compatibility implement lcm manually: "
                        "def lcm(a, b): return abs(a*b) // math.gcd(a, b)"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/math.html#math.lcm"
                    ),
                ))
        return findings