"""CPY032 -- typing.reveal_type requires Python 3.11+.

Evidence note (corrected 2026-09-13): earlier releases of this rule cited
PEP 544 as the authoritative source. PEP 544 specifies structural typing
(Protocols) and is unrelated to ``reveal_type``. ``typing.reveal_type``
is a Python 3.11 typing-module addition (previously a type-checker-only
convention) documented in the official typing documentation and the
3.11 "What's New" notes; there is no dedicated PEP for it. See
``pyrift.rule_metadata`` for the corresponding metadata fix.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class RevealTypeRule(BaseRule):
    rule_id = "CPY032"
    title = "typing.reveal_type requires Python 3.11+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            if info.module == "typing" and info.name == "reveal_type" and not (info.version_guarded and info.version_guarded >= (3, 11)):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description="typing.reveal_type requires Python 3.11+. Raises ImportError on Python 3.10 and below.",
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.10",
                    suggestion="Guard with: if sys.version_info >= (3, 11): from typing import reveal_type -- or use typing_extensions.",
                    docs_url="https://docs.python.org/3/library/typing.html#typing.reveal_type",
                ))
        return findings