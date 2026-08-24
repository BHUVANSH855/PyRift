"""
CPY015 — typing.Never requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
typing.Never was added in Python 3.11 (PEP 673).
Using it on 3.10 or below raises ImportError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class NeverRule(BaseRule):
    rule_id = "CPY015"
    title   = "typing.Never requires Python 3.11+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.ImportFrom) and n.module == "typing":
                for alias in n.names:
                    if alias.name == "Never":
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                "typing.Never was added in Python 3.11 "
                                "(PEP 673). Importing it on Python 3.10 "
                                "or below raises ImportError at runtime."
                            ),
                            severity=Severity.ERROR,
                            runtime=Runtime.CPYTHON,
                            affected_from="3.0",
                            affected_until="3.10",
                            suggestion=(
                                "Guard with: if sys.version_info >= (3, 11): "
                                "from typing import Never "
                                "else: from typing_extensions import Never"
                            ),
                            docs_url="https://peps.python.org/pep-0673/",
                        ))
        return findings