"""
CPY090 -- profile module deprecated in favour of cProfile (3.15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The pure-Python ``profile`` module was soft-deprecated in Python 3.15.
``cProfile`` is the recommended replacement and has been available since
Python 2.5.

    import profile                 # deprecated 3.15
    from profile import Profile    # deprecated 3.15
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ProfileDeprecatedRule(BaseRule):
    rule_id = "CPY090"
    title = "profile module deprecated in Python 3.15 — use cProfile"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for imp in collect_imports(node).imports:
            if imp.module == "profile":
                findings.append(Finding(
                    file=filename,
                    line=imp.line,
                    col=imp.col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The pure-Python 'profile' module was deprecated "
                        "in Python 3.15. It carries significant overhead "
                        "compared to 'cProfile', which is implemented in C "
                        "and has been available since Python 2.5."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.15",
                    suggestion=(
                        "Replace 'import profile' with 'import cProfile'. "
                        "The public API (Profile class, run(), runctx()) "
                        "is identical."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.15.html"
                        "#deprecated"
                    ),
                ))
        return findings