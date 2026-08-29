"""
CPY047 — collections.abc.ByteString removed in Python 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
collections.abc.ByteString was deprecated in Python 3.12 and
removed in Python 3.15. Using it raises AttributeError on 3.15+.
Use Union[bytes, bytearray, memoryview] instead.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ByteStringRemovedRule(BaseRule):
    rule_id = "CPY047"
    title   = "collections.abc.ByteString removed in Python 3.15"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # Detect: from collections.abc import ByteString
            if isinstance(n, ast.ImportFrom) and n.module in ("collections.abc", "collections"):
                    for alias in n.names:
                        if alias.name == "ByteString":
                            findings.append(Finding(
                                file=filename,
                                line=n.lineno,
                                col=n.col_offset,
                                rule_id=self.rule_id,
                                title=self.title,
                                description=(
                                    "collections.abc.ByteString was deprecated "
                                    "in Python 3.12 and removed in Python 3.15. "
                                    "Importing it on Python 3.15+ raises "
                                    "ImportError at runtime."
                                ),
                                severity=Severity.ERROR,
                                runtime=Runtime.CPYTHON,
                                affected_from="3.15",
                                suggestion=(
                                    "Replace with: Union[bytes, bytearray, memoryview] "
                                    "or use the specific type you actually need. "
                                    "from typing import Union"
                                ),
                                docs_url=(
                                    "https://docs.python.org/3/whatsnew/3.15.html"
                                ),
                            ))
            # Detect: collections.abc.ByteString attribute access
            if isinstance(n, ast.Attribute) and n.attr == "ByteString":
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "collections.abc.ByteString was deprecated in "
                        "Python 3.12 and removed in Python 3.15. "
                        "Accessing it on Python 3.15+ raises AttributeError."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.15",
                    suggestion=(
                        "Replace with: Union[bytes, bytearray, memoryview]"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.15.html"
                    ),
                ))
        return findings