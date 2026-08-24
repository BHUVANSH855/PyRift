"""
CPY002 — Exception.add_note() requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Exception.add_note() was added in CPython 3.11 (PEP 678).
Code using it silently fails with AttributeError on 3.10 and below.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class ExceptionNotesRule(BaseRule):
    rule_id = "CPY002"
    title   = "Exception.add_note() requires Python 3.11+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if isinstance(func, ast.Attribute) and func.attr == "add_note":
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "Exception.add_note() was introduced in Python 3.11 "
                        "(PEP 678). Calling it on Python 3.10 or earlier raises "
                        "AttributeError at runtime — a silent compatibility break "
                        "if your code targets multiple Python versions."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.10",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 11): e.add_note(...) "
                        "or append context to the exception message manually for 3.10."
                    ),
                    docs_url="https://peps.python.org/pep-0678/",
                ))

        return findings