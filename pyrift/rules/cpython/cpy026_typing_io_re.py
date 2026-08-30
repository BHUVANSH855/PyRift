"""CPY026 -- typing.io and typing.re removed in Python 3.13."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

REMOVED_NAMESPACES = {"typing.io", "typing.re"}


class TypingIoReRule(BaseRule):
    rule_id = "CPY026"
    title = "typing.io and typing.re removed in Python 3.13"
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
            if info.module in REMOVED_NAMESPACES:
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        f"The {info.module} namespace was an undocumented "
                        "sub-namespace of typing that was removed in Python 3.13. "
                        "Importing from it raises ImportError on Python 3.13+."
                    ),
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "Import directly from typing instead: "
                        "from typing import IO, Pattern, Match"
                    ),
                    docs_url="https://docs.python.org/3/library/typing.html",
                ))
        return findings