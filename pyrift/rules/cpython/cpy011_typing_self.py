"""CPY011 -- typing.Self requires Python 3.11+ (PEP 673)."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class TypingSelfRule(BaseRule):
    rule_id = "CPY011"
    title = "typing.Self requires Python 3.11+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            if info.module == "typing" and info.name == "Self" and not (info.version_guarded and info.version_guarded >= (3, 11)):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description="typing.Self requires Python 3.11+. Raises ImportError on Python 3.10 and below.",
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.10",
                    suggestion="Guard with: if sys.version_info >= (3, 11): from typing import Self -- or use typing_extensions.",
                    docs_url="https://peps.python.org/pep-673/",
                ))
        return findings