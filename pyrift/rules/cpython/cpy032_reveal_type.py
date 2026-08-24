"""
CPY032 — typing.reveal_type requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
typing.reveal_type was added as a proper stdlib function in Python
3.11. Before 3.11, reveal_type was only a special form recognised
by type checkers — calling it at runtime raises NameError on 3.10-.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class RevealTypeRule(BaseRule):
    rule_id = "CPY032"
    title   = "typing.reveal_type requires Python 3.11+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.ImportFrom) and n.module == "typing":
                for alias in n.names:
                    if alias.name == "reveal_type":
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                "typing.reveal_type was added to the stdlib "
                                "in Python 3.11. Before 3.11, reveal_type was "
                                "only recognised by type checkers as a special "
                                "form — importing it from typing on 3.10 or "
                                "below raises ImportError at runtime."
                            ),
                            severity=Severity.ERROR,
                            runtime=Runtime.CPYTHON,
                            affected_from="3.0",
                            affected_until="3.10",
                            suggestion=(
                                "Guard with: if sys.version_info >= (3, 11): "
                                "from typing import reveal_type "
                                "else: from typing_extensions import reveal_type"
                            ),
                            docs_url=(
                                "https://docs.python.org/3/library/typing.html"
                                "#typing.reveal_type"
                            ),
                        ))
        return findings