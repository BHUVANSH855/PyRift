"""CPY063 -- annotationlib requires Python 3.14+."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class AnnotationLibRule(BaseRule):
    rule_id = "CPY063"
    title = "annotationlib requires Python 3.14+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        imp_map = collect_imports(node)
        for info in imp_map.imports:
            if info.module == "annotationlib" or (info.module and info.module.startswith("annotationlib")):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description="annotationlib was added in Python 3.14 (PEP 749). Importing it on 3.13 or below raises ModuleNotFoundError.",
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.13",
                    suggestion="Guard with: if sys.version_info >= (3, 14): import annotationlib -- for 3.13, use typing.get_type_hints()",
                    docs_url="https://peps.python.org/pep-0749/",
                ))
        return findings
