"""
CPY026 — typing.io and typing.re namespaces removed in Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The typing.io and typing.re sub-namespaces were deprecated in
Python 3.12 and removed in Python 3.13. They were undocumented
aliases. Importing from them raises ImportError on 3.13+.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime

REMOVED_NAMESPACES = {"typing.io", "typing.re"}


class TypingIoReRule(BaseRule):
    rule_id = "CPY026"
    title   = "typing.io and typing.re removed in Python 3.13"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.ImportFrom):
                if n.module in REMOVED_NAMESPACES:
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"'{n.module}' is an undocumented sub-namespace "
                            "of the typing module that was deprecated in "
                            "Python 3.12 and removed in Python 3.13. "
                            "Importing from it raises ImportError on 3.13+."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.13",
                        suggestion=(
                            "Import directly from typing instead: "
                            "'from typing import IO, TextIO, BinaryIO' "
                            "for typing.io, or 'from typing import Pattern, Match' "
                            "for typing.re."
                        ),
                        docs_url=(
                            "https://docs.python.org/3/whatsnew/3.13.html"
                        ),
                    ))
        return findings