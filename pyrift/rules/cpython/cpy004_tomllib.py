"""
CPY004 — tomllib requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
tomllib was added to the stdlib in Python 3.11 (PEP 680).
Importing it on 3.10 or below raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class TomllibRule(BaseRule):
    rule_id = "CPY004"
    title   = "tomllib requires Python 3.11+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "tomllib":
                        findings.append(self._make(filename, n.lineno, n.col_offset))
            elif isinstance(n, ast.ImportFrom) and n.module == "tomllib":
                findings.append(self._make(filename, n.lineno, n.col_offset))

        return findings

    def _make(self, filename: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename,
            line=line,
            col=col,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "tomllib was added to the Python standard library in 3.11 "
                "(PEP 680). Importing it on Python 3.10 or earlier raises "
                "ModuleNotFoundError at runtime."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.0",
            affected_until="3.10",
            suggestion=(
                "Guard with: if sys.version_info >= (3, 11): import tomllib "
                "else: import tomli as tomllib  "
                "(tomli is a backport: pip install tomli)"
            ),
            docs_url="https://peps.python.org/pep-0680/",
        )