"""CPY013 -- typing.override requires Python 3.12+ (PEP 698)."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class OverrideRule(BaseRule):
    rule_id = "CPY013"
    title = "typing.override requires Python 3.12+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            if info.module == "typing" and info.name == "override":
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description="typing.override requires Python 3.12+. Raises ImportError on Python 3.11 and below.",
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.11",
                    suggestion="Guard with: if sys.version_info >= (12,): from typing import override -- or use typing_extensions.",
                    docs_url="https://peps.python.org/pep-698/",
                ))
        return findings
