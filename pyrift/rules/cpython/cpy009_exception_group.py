"""
CPY009 — ExceptionGroup requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ExceptionGroup and BaseExceptionGroup were introduced in Python 3.11
(PEP 654). Using them on 3.10 or below raises NameError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

EXCEPTION_GROUP_NAMES = {"ExceptionGroup", "BaseExceptionGroup"}


class ExceptionGroupRule(BaseRule):
    rule_id = "CPY009"
    title   = "ExceptionGroup requires Python 3.11+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if isinstance(n, ast.Name) and n.id in EXCEPTION_GROUP_NAMES:
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"{n.id} was introduced in Python 3.11 (PEP 654). "
                        "On Python 3.10 and below, using it raises NameError "
                        "at runtime — it does not exist as a built-in."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.10",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 11): "
                        "or use the exceptiongroup backport package "
                        "(pip install exceptiongroup) for 3.10 compatibility."
                    ),
                    docs_url="https://peps.python.org/pep-0654/",
                ))

        return findings