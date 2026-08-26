"""CPY019 -- distutils removed in Python 3.12+ (PEP 632)."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

DISTUTILS_MODULES = {
    "distutils", "distutils.core", "distutils.cmd",
    "distutils.command", "distutils.dist", "distutils.extension",
    "distutils.fancy_getopt", "distutils.file_util",
    "distutils.log", "distutils.spawn", "distutils.sysconfig",
    "distutils.text_file", "distutils.unixccompiler",
    "distutils.util", "distutils.version",
}


class DistutilsRule(BaseRule):
    rule_id = "CPY019"
    title = "distutils removed in Python 3.12+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        imp_map = collect_imports(node)
        for info in imp_map.by_statement():
            mod = info.module or ""
            if mod in DISTUTILS_MODULES or mod.startswith("distutils."):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        f"distutils (imported as '{mod}') was deprecated in "
                        "Python 3.10 and removed in Python 3.12 (PEP 632). "
                        "Importing it on Python 3.12+ raises ModuleNotFoundError."
                    ),
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        "Replace with setuptools: pip install setuptools. "
                        "Most distutils functionality is available in "
                        "setuptools or the standard build tools."
                    ),
                    docs_url="https://peps.python.org/pep-0632/",
                ))
        return findings
