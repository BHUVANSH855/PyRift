"""
CPY019 — distutils removed in Python 3.12
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The distutils package was removed from the standard library in
Python 3.12 (PEP 632). Importing it raises ModuleNotFoundError.
It was deprecated in Python 3.10.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

DISTUTILS_MODULES = {
    "distutils",
    "distutils.core",
    "distutils.cmd",
    "distutils.command",
    "distutils.util",
    "distutils.version",
    "distutils.errors",
    "distutils.log",
    "distutils.dist",
    "distutils.extension",
}


class DistutilsRule(BaseRule):
    rule_id = "CPY019"
    title   = "distutils removed in Python 3.12+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name in DISTUTILS_MODULES or \
                       alias.name.startswith("distutils."):
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom):
                if n.module and (n.module in DISTUTILS_MODULES or
                                 n.module.startswith("distutils")):
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
                        f"'{mod}' is part of the distutils package which was "
                        "removed from the Python standard library in Python 3.12 "
                        "(PEP 632). Importing it on Python 3.12+ raises "
                        "ModuleNotFoundError."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        "Replace distutils with setuptools: "
                        "pip install setuptools. "
                        "Most distutils APIs have direct equivalents in setuptools."
                    ),
                    docs_url="https://peps.python.org/pep-0632/",
                ))
        return findings