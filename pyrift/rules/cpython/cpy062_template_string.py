"""
CPY062 — string.templatelib requires Python 3.14+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The string.templatelib module (t-strings, PEP 750) was added in
Python 3.14. Importing it on Python 3.13 or below raises
ModuleNotFoundError. T-strings are a new literal prefix 't"..."'
that creates Template objects instead of plain strings.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class TemplateStringRule(BaseRule):
    rule_id = "CPY062"
    title   = "string.templatelib requires Python 3.14+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "string.templatelib":
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom) and n.module == "string.templatelib":
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
                        "string.templatelib was added in Python 3.14 (PEP 750). "
                        "It provides support for t-string template literals "
                        "which create Template objects instead of plain strings. "
                        "Importing it on Python 3.13 or below raises "
                        "ModuleNotFoundError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.13",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 14): "
                        "from string.templatelib import Template, Interpolation "
                        "T-strings are not backportable — use f-strings "
                        "or string.Template for Python 3.13 compatibility."
                    ),
                    docs_url="https://peps.python.org/pep-0750/",
                ))
        return findings