"""CPY048 -- concurrent.interpreters requires Python 3.14+."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class ConcurrentInterpretersRule(BaseRule):
    rule_id = "CPY048"
    title = "concurrent.interpreters requires Python 3.14+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        imp_map = collect_imports(node)
        for info in imp_map.by_statement():
            if info.module == "concurrent.interpreters" or (info.module and info.module.startswith("concurrent.interpreters")):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description="concurrent.interpreters was added in Python 3.14 (PEP 734). Importing it on 3.13 or below raises ModuleNotFoundError.",
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.13",
                    suggestion="Guard with: if sys.version_info >= (3, 14): import concurrent.interpreters",
                    docs_url="https://peps.python.org/pep-0734/",
                ))
        return findings
