"""
CPY036 — datetime.datetime.utcnow() deprecated in Python 3.12
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
datetime.datetime.utcnow() was deprecated in Python 3.12 because
it returns a naive datetime with no timezone info, making it easy
to confuse with local time. It will be removed in a future version.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class DatetimeUtcnowRule(BaseRule):
    rule_id = "CPY036"
    title   = "datetime.utcnow() deprecated since Python 3.12"
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
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "utcnow"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "datetime.datetime.utcnow() is deprecated since "
                        "Python 3.12. It returns a naive datetime object "
                        "with no timezone information, making it dangerously "
                        "easy to confuse with local time. It will be removed "
                        "in a future Python version."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        "Use datetime.datetime.now(datetime.timezone.utc) "
                        "which returns a timezone-aware UTC datetime. "
                        "Or with Python 3.11+: datetime.datetime.now(datetime.UTC)"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/datetime.html"
                        "#datetime.datetime.utcnow"
                    ),
                ))
        return findings