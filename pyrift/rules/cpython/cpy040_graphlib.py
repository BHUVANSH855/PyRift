"""
CPY040 -- graphlib module requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The graphlib module was added in Python 3.9.
On Python 3.8 and below, importing graphlib raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class GraphlibRule(BaseRule):
    rule_id = "CPY040"
    title = "graphlib module requires Python 3.9+"
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

        for info in imp_map.get("graphlib"):
            findings.append(Finding(
                file=filename,
                line=info.line,
                col=info.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "The graphlib module (TopologicalSorter) was added "
                    "in Python 3.9. On Python 3.8 and below, importing "
                    "graphlib raises ModuleNotFoundError."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.0",
                affected_until="3.8",
                suggestion=(
                    "Guard with: "
                    "if sys.version_info >= (3, 9): from graphlib import TopologicalSorter "
                    "Or implement topological sort manually for 3.8 support."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/graphlib.html"
                ),
            ))

        return findings