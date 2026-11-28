"""
CPY079 -- typing.ByteString / collections.abc.ByteString deprecated,
          scheduled for removal in Python 3.17
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``typing.ByteString`` was deprecated in Python 3.9 and
``collections.abc.ByteString`` was deprecated in Python 3.12.
Both are scheduled for removal in Python 3.17.  In Python 3.15 they were
removed from their respective ``__all__`` lists and accessing them now
emits a ``DeprecationWarning``.

    from typing import ByteString          # deprecated 3.9, removed 3.17
    from collections.abc import ByteString # deprecated 3.12, removed 3.17

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
    title = "typing.ByteString / collections.abc.ByteString deprecated, removed in Python 3.17"
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
                # typing.ByteString deprecated 3.9; collections.abc.ByteString deprecated 3.12
                dep_ver = "3.9" if mod == "typing" else "3.12"
                findings.append(Finding(
                    file=filename,
                    line=info.line,
                    col=info.col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"'{mod}.ByteString' was deprecated in Python {dep_ver} "
                        "and is scheduled for removal in Python 3.17. "
                        "In Python 3.15 it was removed from __all__ and now "
                        "emits a DeprecationWarning on import."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from=dep_ver,
                    affected_until="3.17",
                    suggestion=(
                        "Replace with 'bytes | bytearray | memoryview' for "
                        "type hints, or use 'collections.abc.Buffer' "
                        "(available from Python 3.12)."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/deprecations/"
                        "pending-removal-in-3.17.html"
                    ),
                ))
        return findings