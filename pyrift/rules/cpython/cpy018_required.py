"""CPY018 -- typing.Required / NotRequired requires Python 3.11+ (PEP 655)."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

TARGETS = {"Required", "NotRequired"}


class RequiredRule(BaseRule):
    rule_id = "CPY018"
    title = "typing.Required / NotRequired requires Python 3.11+"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            if info.module == "typing" and info.name in TARGETS and not (info.version_guarded and info.version_guarded >= (3, 11)):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        f"typing.{info.name} requires Python 3.11+ (PEP 655). "
                        "Importing it on Python 3.10 or below raises ImportError."
                    ),
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.10",
                    suggestion=(
                        f"try: from typing import {info.name} "
                        f"except ImportError: from typing_extensions import {info.name}"
                    ),
                    docs_url="https://peps.python.org/pep-0655/",
                ))
        return findings