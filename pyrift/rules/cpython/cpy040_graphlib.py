"""
CPY040 — graphlib module requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The graphlib module (with TopologicalSorter) was added in Python 3.9.
Importing it on Python 3.8 or below raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class GraphlibRule(BaseRule):
    rule_id = "CPY040"
    title   = "graphlib module requires Python 3.9+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "graphlib":
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom):
                if n.module == "graphlib":
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
                        "The graphlib module was added in Python 3.9. "
                        "It provides TopologicalSorter for dependency "
                        "resolution. Importing it on Python 3.8 or below "
                        "raises ModuleNotFoundError."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.8",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 9): "
                        "from graphlib import TopologicalSorter "
                        "For 3.8 compatibility, implement topological sort "
                        "manually or use the graphlib2 backport on PyPI."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/graphlib.html"
                    ),
                ))
        return findings