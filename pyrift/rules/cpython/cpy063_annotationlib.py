"""
CPY063 — annotationlib requires Python 3.14+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The annotationlib module (PEP 749) was added in Python 3.14 to
support the new deferred annotation evaluation (PEP 649).
Importing it on Python 3.13 or below raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class AnnotationLibRule(BaseRule):
    rule_id = "CPY063"
    title   = "annotationlib requires Python 3.14+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "annotationlib":
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom) and n.module == "annotationlib":
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
                        "annotationlib was added in Python 3.14 (PEP 749). "
                        "It provides tools for introspecting deferred "
                        "annotations introduced by PEP 649. Importing it "
                        "on Python 3.13 or below raises ModuleNotFoundError."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.13",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 14): "
                        "import annotationlib "
                        "For 3.13 compatibility, use typing.get_type_hints() "
                        "for annotation introspection instead."
                    ),
                    docs_url="https://peps.python.org/pep-0749/",
                ))
        return findings