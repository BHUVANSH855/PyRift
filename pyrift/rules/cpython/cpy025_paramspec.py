"""CPY025 -- typing.ParamSpec requires Python 3.10+ (PEP 612)."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ParamSpecRule(BaseRule):
    rule_id = "CPY025"
    title = "typing.ParamSpec requires Python 3.10+"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            if info.module == "typing" and info.name == "ParamSpec" and not (info.version_guarded and info.version_guarded >= (3, 10)):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description="typing.ParamSpec requires Python 3.10+. Raises ImportError on Python 3.9 and below.",
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.9",
                    suggestion="Guard with: if sys.version_info >= (3, 10): from typing import ParamSpec -- or use typing_extensions.",
                    docs_url="https://peps.python.org/pep-612/",
                ))
        return findings