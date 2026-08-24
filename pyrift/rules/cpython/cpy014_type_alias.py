"""
CPY014 — typing.TypeAlias requires Python 3.10+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
typing.TypeAlias was added in Python 3.10 (PEP 613).
Using it on 3.9 or below raises ImportError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class TypeAliasRule(BaseRule):
    rule_id = "CPY014"
    title   = "typing.TypeAlias requires Python 3.10+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.ImportFrom) and n.module == "typing":
                for alias in n.names:
                    if alias.name == "TypeAlias":
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                "typing.TypeAlias was added in Python 3.10 "
                                "(PEP 613). Importing it on Python 3.9 or "
                                "below raises ImportError at runtime."
                            ),
                            severity=Severity.ERROR,
                            runtime=Runtime.CPYTHON,
                            affected_from="3.0",
                            affected_until="3.9",
                            suggestion=(
                                "Guard with: if sys.version_info >= (3, 10): "
                                "from typing import TypeAlias "
                                "else: from typing_extensions import TypeAlias"
                            ),
                            docs_url="https://peps.python.org/pep-0613/",
                        ))
        return findings