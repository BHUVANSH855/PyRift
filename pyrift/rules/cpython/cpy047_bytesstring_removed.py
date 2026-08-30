"""
CPY047 — collections.abc.ByteString deprecated, scheduled removal in 3.17
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
collections.abc.ByteString was deprecated in Python 3.12 and is
scheduled for removal in Python 3.17. Using it on 3.15+ raises
DeprecationWarning; using it after 3.17 will raise AttributeError.
Use Union[bytes, bytearray, memoryview] instead.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ByteStringRemovedRule(BaseRule):
    rule_id = "CPY047"
    title   = "collections.abc.ByteString deprecated, scheduled removal in Python 3.17"
    runtime = "cpython"
    severity = Severity.WARNING

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
                                    "in Python 3.12 and is scheduled for removal "
                                    "in Python 3.17. It emits DeprecationWarning "
                                    "on Python 3.15+."
                                ),
                                severity=Severity.WARNING,
                                runtime=Runtime.CPYTHON,
                                affected_from="3.15",
                                affected_until="3.17",
                                suggestion=(
                                    "Replace with: Union[bytes, bytearray, memoryview] "
                                    "or use the specific type you actually need. "
                                    "from typing import Union"
                                ),
                                docs_url=(
                                    "https://docs.python.org/3/whatsnew/3.12.html"
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
                        "Python 3.12 and is scheduled for removal in "
                        "Python 3.17. It emits DeprecationWarning on "
                        "Python 3.15+."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.15",
                    affected_until="3.17",
                    suggestion=(
                        "Replace with: Union[bytes, bytearray, memoryview]"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.12.html"
                    ),
                ))
        return findings