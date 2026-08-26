"""CPY031 -- typing.assert_never requires Python 3.11+ (PEP 673)."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class AssertNeverRule(BaseRule):
    rule_id = "CPY031"
    title = "typing.assert_never requires Python 3.11+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            if info.module == "typing" and info.name == "assert_never":
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description="typing.assert_never requires Python 3.11+. Raises ImportError on Python 3.10 and below.",
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.10",
                    suggestion="Guard with: if sys.version_info >= (11,): from typing import assert_never -- or use typing_extensions.",
                    docs_url="https://peps.python.org/pep-673/",
                ))
        return findings
