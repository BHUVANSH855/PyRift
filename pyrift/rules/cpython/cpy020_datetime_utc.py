"""
CPY020 — datetime.UTC requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
datetime.UTC was added as a convenience alias for datetime.timezone.utc
in Python 3.11. Using it on 3.10 or below raises AttributeError.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class DatetimeUTCRule(BaseRule):
    rule_id = "CPY020"
    title   = "datetime.UTC requires Python 3.11+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.Attribute):
                if (n.attr == "UTC" and
                        isinstance(n.value, ast.Name) and
                        n.value.id == "datetime"):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "datetime.UTC was added in Python 3.11 as a "
                            "shorthand for datetime.timezone.utc. "
                            "On Python 3.10 and below this raises "
                            "AttributeError at runtime."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.0",
                        affected_until="3.10",
                        suggestion=(
                            "Use datetime.timezone.utc instead — "
                            "it works on all Python 3 versions."
                        ),
                        docs_url=(
                            "https://docs.python.org/3/library/datetime.html"
                            "#datetime.UTC"
                        ),
                    ))
        return findings