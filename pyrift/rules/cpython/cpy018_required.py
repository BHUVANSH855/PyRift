"""
CPY018 — typing.Required / NotRequired requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
typing.Required and typing.NotRequired were added in Python 3.11
(PEP 655). Using them on 3.10 or below raises ImportError.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class RequiredRule(BaseRule):
    rule_id = "CPY018"
    title   = "typing.Required / NotRequired requires Python 3.11+"
    runtime = "cpython"

    TARGETS = {"Required", "NotRequired"}

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.ImportFrom) and n.module == "typing":
                for alias in n.names:
                    if alias.name in self.TARGETS:
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                f"typing.{alias.name} was added in Python 3.11 "
                                "(PEP 655). Importing it on Python 3.10 "
                                "or below raises ImportError at runtime."
                            ),
                            severity=Severity.ERROR,
                            runtime=Runtime.CPYTHON,
                            affected_from="3.0",
                            affected_until="3.10",
                            suggestion=(
                                f"Guard with: if sys.version_info >= (3, 11): "
                                f"from typing import {alias.name} "
                                f"else: from typing_extensions import {alias.name}"
                            ),
                            docs_url="https://peps.python.org/pep-0655/",
                        ))
        return findings