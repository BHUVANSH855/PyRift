"""
CPY053 — typing.get_overloads() requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
typing.get_overloads() was added in Python 3.11. Calling it on
Python 3.10 or below raises AttributeError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class TypingGetOverloadsRule(BaseRule):
    rule_id = "CPY053"
    title   = "typing.get_overloads() requires Python 3.11+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # Detect: from typing import get_overloads
            if isinstance(n, ast.ImportFrom) and n.module == "typing":
                for alias in n.names:
                    if alias.name == "get_overloads":
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                "typing.get_overloads() was added in Python 3.11. "
                                "Importing it on Python 3.10 or below raises "
                                "ImportError at runtime."
                            ),
                            severity=Severity.ERROR,
                            runtime=Runtime.CPYTHON,
                            affected_from="3.0",
                            affected_until="3.10",
                            suggestion=(
                                "Guard with: if sys.version_info >= (3, 11): "
                                "from typing import get_overloads "
                                "else: from typing_extensions import get_overloads"
                            ),
                            docs_url=(
                                "https://docs.python.org/3/library/typing.html"
                                "#typing.get_overloads"
                            ),
                        ))
            # Detect: typing.get_overloads() call
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Attribute) and
                        func.attr == "get_overloads" and
                        isinstance(func.value, ast.Name) and
                        func.value.id == "typing"):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "typing.get_overloads() was added in Python 3.11. "
                            "Calling it on Python 3.10 or below raises "
                            "AttributeError at runtime."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.0",
                        affected_until="3.10",
                        suggestion=(
                            "Guard with: if sys.version_info >= (3, 11): "
                            "from typing import get_overloads"
                        ),
                        docs_url=(
                            "https://docs.python.org/3/library/typing.html"
                            "#typing.get_overloads"
                        ),
                    ))
        return findings