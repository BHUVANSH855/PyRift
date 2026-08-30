"""
CPY039 -- zoneinfo module requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The zoneinfo module was added in Python 3.9 (PEP 615).
On Python 3.8 and below, importing zoneinfo raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ZoneInfoRule(BaseRule):
    rule_id = "CPY039"
    title = "zoneinfo module requires Python 3.9+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        imp_map = collect_imports(node)
        findings: list[Finding] = []

        for info in imp_map.get("zoneinfo"):
            findings.append(Finding(
                file=filename,
                line=info.line,
                col=info.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "The zoneinfo module was added in Python 3.9 "
                    "(PEP 615). On Python 3.8 and below, importing "
                    "zoneinfo raises ModuleNotFoundError."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.0",
                affected_until="3.8",
                suggestion=(
                    "For Python 3.8 compatibility use the backport: "
                    "try: from zoneinfo import ZoneInfo "
                    "except ImportError: from backports.zoneinfo import ZoneInfo "
                    "(pip install backports.zoneinfo)"
                ),
                docs_url="https://peps.python.org/pep-0615/",
            ))

        return findings