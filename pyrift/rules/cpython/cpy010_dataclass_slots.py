"""
CPY010 — @dataclass(slots=True) requires Python 3.10+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The slots parameter for @dataclass was added in Python 3.10.
Using it on 3.9 or below raises TypeError at class definition time.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class DataclassSlotsRule(BaseRule):
    rule_id = "CPY010"
    title   = "@dataclass(slots=True) requires Python 3.10+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.ClassDef):
                continue

            for decorator in n.decorator_list:
                # Looking for @dataclass(slots=True) or @dataclasses.dataclass(slots=True)
                if not isinstance(decorator, ast.Call):
                    continue

                func = decorator.func
                is_dataclass = False
                if isinstance(func, ast.Name) and func.id == "dataclass" or (isinstance(func, ast.Attribute) and
                      func.attr == "dataclass"):
                    is_dataclass = True

                if not is_dataclass:
                    continue

                for kw in decorator.keywords:
                    if kw.arg == "slots" and isinstance(kw.value, ast.Constant) and kw.value.value:
                            findings.append(Finding(
                                file=filename,
                                line=decorator.lineno,
                                col=decorator.col_offset,
                                rule_id=self.rule_id,
                                title=self.title,
                                description=(
                                    "The slots=True parameter for @dataclass "
                                    "was added in Python 3.10. On Python 3.9 "
                                    "and below, this raises TypeError at class "
                                    "definition time — not at instantiation."
                                ),
                                severity=Severity.ERROR,
                                runtime=Runtime.CPYTHON,
                                affected_from="3.0",
                                affected_until="3.9",
                                suggestion=(
                                    "Remove slots=True and define __slots__ "
                                    "manually for Python 3.9 compatibility, "
                                    "or add requires-python = '>=3.10' to "
                                    "your pyproject.toml."
                                ),
                                docs_url=(
                                    "https://docs.python.org/3/library/"
                                    "dataclasses.html"
                                ),
                            ))

        return findings