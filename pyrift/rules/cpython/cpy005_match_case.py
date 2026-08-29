"""
CPY005 — match/case structural pattern matching requires Python 3.10+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PEP 634 introduced match/case in 3.10. Using it on 3.9 or below
is a SyntaxError — the file won't even import.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class MatchCaseRule(BaseRule):
    rule_id = "CPY005"
    title   = "match/case requires Python 3.10+"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # ast.Match was added in Python 3.10
            if isinstance(n, ast.Match):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "Structural pattern matching (match/case) was introduced "
                        "in Python 3.10 (PEP 634). On Python 3.9 and below this "
                        "is a SyntaxError — the entire module fails to import."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.9",
                    suggestion=(
                        "Replace with if/elif chains for Python 3.9 compatibility, "
                        "or add requires-python = '>=3.10' to your pyproject.toml."
                    ),
                    docs_url="https://peps.python.org/pep-0634/",
                ))

        return findings