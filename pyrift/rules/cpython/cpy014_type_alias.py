"""CPY014 -- typing.TypeAlias requires Python 3.10+ (PEP 613)."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class TypeAliasRule(BaseRule):
    rule_id = "CPY014"
    title = "typing.TypeAlias requires Python 3.10+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            if info.module == "typing" and info.name == "TypeAlias":
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description="typing.TypeAlias requires Python 3.10+. Raises ImportError on Python 3.9 and below.",
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.9",
                    suggestion="Guard with: if sys.version_info >= (10,): from typing import TypeAlias -- or use typing_extensions.",
                    docs_url="https://peps.python.org/pep-613/",
                ))
        return findings
