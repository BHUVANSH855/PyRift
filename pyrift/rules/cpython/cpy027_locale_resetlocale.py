"""
CPY027 — locale.resetlocale() removed in Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
locale.resetlocale() was deprecated in Python 3.11 and removed
in Python 3.13. Calling it raises AttributeError on 3.13+.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class LocaleResetlocaleRule(BaseRule):
    rule_id = "CPY027"
    title   = "locale.resetlocale() removed in Python 3.13"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "resetlocale" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "locale"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "locale.resetlocale() was deprecated in Python 3.11 "
                        "and removed in Python 3.13. Calling it on Python "
                        "3.13+ raises AttributeError."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "Replace with: locale.setlocale(locale.LC_ALL, '') "
                        "which resets the locale to the system default "
                        "and works on all Python 3 versions."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.13.html"
                    ),
                ))
        return findings