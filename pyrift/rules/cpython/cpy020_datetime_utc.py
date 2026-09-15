"""
CPY020 -- datetime.UTC requires Python 3.11+.

The rule reports uses of the stdlib ``datetime.UTC`` constant and
``from datetime import UTC``.  It deliberately requires evidence that
``datetime`` refers to the stdlib module instead of flagging arbitrary
attributes named ``UTC`` on unrelated objects.
"""

from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class DatetimeUTCRule(BaseRule):
    rule_id = "CPY020"
    title = "datetime.UTC requires Python 3.11+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        imports = collect_imports(node)

        # Module imports:
        #   import datetime
        #   import datetime as dt
        datetime_aliases = {
            info.alias or "datetime"
            for info in imports.imports
            if info.module == "datetime" and info.name is None
        }

        # Direct imports:
        #   from datetime import UTC
        direct_utc_imports = [
            info
            for info in imports.imports
            if info.module == "datetime" and info.name == "UTC"
        ]

        reported_nodes: set[int] = set()

        for n in ast.walk(node):
            if not isinstance(n, ast.Attribute):
                continue

            if n.attr != "UTC" or not isinstance(n.value, ast.Name):
                continue

            if n.value.id not in datetime_aliases:
                continue

            reported_nodes.add(id(n))
            findings.append(self._finding(filename, n.lineno, n.col_offset))

        for info in direct_utc_imports:
            node_id = id(info.node)
            if node_id in reported_nodes:
                continue

            findings.append(self._finding(filename, info.line, info.col))

        return findings

    def _finding(
        self,
        filename: str,
        line: int,
        col: int,
    ) -> Finding:
        return Finding(
            file=filename,
            line=line,
            col=col,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "datetime.UTC was added in Python 3.11 as an alias for "
                "datetime.timezone.utc. It is unavailable from the "
                "standard-library datetime module on Python 3.10 and below."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.0",
            affected_until="3.10",
            suggestion=(
                "Use datetime.timezone.utc instead, or use "
                "typing-compatible version guards when supporting "
                "Python 3.10 and earlier."
            ),
            docs_url=("https://docs.python.org/3/library/datetime.html#datetime.UTC"),
        )
