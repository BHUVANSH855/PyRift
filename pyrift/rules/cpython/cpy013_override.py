"""
CPY013 — @override decorator requires Python 3.12+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
typing.override was added in Python 3.12 (PEP 698).
Using it on 3.11 or below raises ImportError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class OverrideRule(BaseRule):
    rule_id = "CPY013"
    title   = "typing.override requires Python 3.12+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if isinstance(n, ast.ImportFrom) and n.module == "typing":
                for alias in n.names:
                    if alias.name == "override":
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                "typing.override was added in Python 3.12 "
                                "(PEP 698). Importing it on Python 3.11 "
                                "or below raises ImportError at runtime."
                            ),
                            severity=Severity.ERROR,
                            runtime=Runtime.CPYTHON,
                            affected_from="3.0",
                            affected_until="3.11",
                            suggestion=(
                                "Guard with: if sys.version_info >= (3, 12): "
                                "from typing import override "
                                "else: from typing_extensions import override"
                            ),
                            docs_url="https://peps.python.org/pep-0698/",
                        ))

        return findings