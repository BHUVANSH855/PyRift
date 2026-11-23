"""
CPY079 -- typing.ByteString / collections.abc.ByteString deprecated (3.12),
          removed in 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Both ``typing.ByteString`` and ``collections.abc.ByteString`` emit a
``DeprecationWarning`` on import from Python 3.12 and are scheduled for
removal in Python 3.15.

    from typing import ByteString          # deprecated 3.12, removed 3.15
    from collections.abc import ByteString # deprecated 3.12, removed 3.15

Use ``bytes | bytearray | memoryview`` or ``collections.abc.Buffer``
(added 3.12) instead.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ByteStringDeprecatedRule(BaseRule):
    rule_id = "CPY079"
    title = "typing.ByteString / collections.abc.ByteString deprecated (3.12), removed (3.15)"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            mod = info.module or ""
            name = info.name or ""
            if name == "ByteString" and mod in (
                "typing",
                "collections.abc",
            ):
                findings.append(Finding(
                    file=filename,
                    line=info.line,
                    col=info.col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"'{mod}.ByteString' was deprecated in Python 3.12 "
                        "and is scheduled for removal in Python 3.15. "
                        "It emits a DeprecationWarning on import in 3.12+."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    affected_until="3.15",
                    suggestion=(
                        "Replace with 'bytes | bytearray | memoryview' for "
                        "type hints, or use 'collections.abc.Buffer' "
                        "(available from Python 3.12)."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.12.html"
                        "#deprecated"
                    ),
                ))
        return findings