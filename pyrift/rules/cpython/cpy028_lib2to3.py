"""
CPY028 — lib2to3 removed in Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The lib2to3 package and 2to3 tool were deprecated in Python 3.11
and removed in Python 3.13. Importing lib2to3 raises ModuleNotFoundError
on Python 3.13+.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class Lib2to3Rule(BaseRule):
    rule_id = "CPY028"
    title   = "lib2to3 removed in Python 3.13"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "lib2to3" or \
                       alias.name.startswith("lib2to3."):
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom):
                if n.module and (n.module == "lib2to3" or
                                 n.module.startswith("lib2to3.")):
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
                        f"'{mod}' is part of lib2to3 which was deprecated "
                        "in Python 3.11 and removed in Python 3.13. "
                        "Importing it raises ModuleNotFoundError on 3.13+."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "Use the 'libcst' or 'fissix' packages as modern "
                        "replacements for lib2to3 functionality. "
                        "pip install libcst"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.13.html"
                    ),
                ))
        return findings