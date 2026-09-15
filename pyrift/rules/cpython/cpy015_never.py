"""CPY015 -- typing.Never requires Python 3.11+."""

from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class NeverRule(BaseRule):
    rule_id = "CPY015"
    title = "typing.Never requires Python 3.11+"
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
            if info.module != "typing" or info.name != "Never":
                continue

            if info.version_guarded and info.version_guarded >= (3, 11):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=info.line,
                    col=info.col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "typing.Never was added in Python 3.11 and is "
                        "not available from the standard-library typing "
                        "module on Python 3.10 and earlier."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.10",
                    suggestion=(
                        "For Python 3.10 and earlier, use "
                        "typing_extensions.Never or guard the import "
                        "with a Python 3.11+ version check."
                    ),
                    docs_url=(
                        "https://docs.python.org/3.11/library/typing.html#typing.Never"
                    ),
                )
            )

        return findings
