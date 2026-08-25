"""
CPY048 — concurrent.interpreters requires Python 3.14+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The concurrent.interpreters module was added in Python 3.14 (PEP 734).
It enables running multiple isolated Python interpreters in the same
process. Importing it on Python 3.13 or below raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class ConcurrentInterpretersRule(BaseRule):
    rule_id = "CPY048"
    title   = "concurrent.interpreters requires Python 3.14+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "concurrent.interpreters":
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom) and n.module == "concurrent.interpreters":
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
                        "concurrent.interpreters was added in Python 3.14 "
                        "(PEP 734). It provides support for running multiple "
                        "isolated Python interpreters in the same process. "
                        "Importing it on Python 3.13 or below raises "
                        "ModuleNotFoundError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.13",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 14): "
                        "import concurrent.interpreters "
                        "For 3.13 compatibility, use multiprocessing or "
                        "threading instead."
                    ),
                    docs_url="https://peps.python.org/pep-0734/",
                ))
        return findings