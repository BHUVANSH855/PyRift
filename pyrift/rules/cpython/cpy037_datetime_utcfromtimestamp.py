"""
CPY037 — datetime.utcfromtimestamp() deprecated in Python 3.12
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
datetime.datetime.utcfromtimestamp() was deprecated in Python 3.12
for the same reason as utcnow() — it returns a naive datetime with
no timezone info. Used extensively in logging and data pipelines.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class DatetimeUtcfromtimestampRule(BaseRule):
    rule_id = "CPY037"
    title   = "datetime.utcfromtimestamp() deprecated since Python 3.12"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "utcfromtimestamp"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "datetime.datetime.utcfromtimestamp() is deprecated "
                        "since Python 3.12. It returns a naive datetime with "
                        "no timezone information. This is a common source of "
                        "timezone bugs in logging, data pipelines, and APIs."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        "Use datetime.datetime.fromtimestamp(ts, datetime.timezone.utc) "
                        "which returns a timezone-aware UTC datetime. "
                        "Works on all Python 3 versions."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/datetime.html"
                        "#datetime.datetime.utcfromtimestamp"
                    ),
                ))
        return findings