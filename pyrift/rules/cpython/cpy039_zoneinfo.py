"""
CPY039 — zoneinfo module requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The zoneinfo module was added in Python 3.9 (PEP 615).
Importing it on Python 3.8 or below raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class ZoneInfoRule(BaseRule):
    rule_id = "CPY039"
    title   = "zoneinfo module requires Python 3.9+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "zoneinfo":
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom) and n.module == "zoneinfo":
                mod = n.module
                line, col = n.lineno, n.col_offset
            if mod:
                findings.append(Finding(
                    file=filename,
                    line=line,
                    col=col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The zoneinfo module was added in Python 3.9 "
                        "(PEP 615). Importing it on Python 3.8 or below "
                        "raises ModuleNotFoundError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.8",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 9): "
                        "import zoneinfo "
                        "else: from backports.zoneinfo import ZoneInfo "
                        "(pip install backports.zoneinfo)"
                    ),
                    docs_url="https://peps.python.org/pep-0615/",
                ))
        return findings