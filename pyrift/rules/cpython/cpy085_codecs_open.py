"""
CPY085 -- codecs.open() deprecated (3.14)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``codecs.open()`` was deprecated in Python 3.14. Use the built-in
``open()`` with an ``encoding=`` argument instead.

    codecs.open('file.txt', 'r', 'utf-8')           # deprecated 3.14
    open('file.txt', 'r', encoding='utf-8')         # correct
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class CodecsOpenRule(BaseRule):
    rule_id = "CPY085"
    title = "codecs.open() deprecated in Python 3.14, use open() with encoding="
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for call in collect_calls(node, "open", module="codecs"):
            findings.append(Finding(
                file=filename,
                line=call.line,
                col=call.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "codecs.open() was deprecated in Python 3.14. "
                    "The built-in open() supports encoding directly "
                    "and is the recommended replacement."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.14",
                suggestion=(
                    "Replace codecs.open(path, mode, encoding) with "
                    "open(path, mode, encoding=encoding). "
                    "The built-in open() also supports errors= and "
                    "newline= for full control."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/functions.html"
                    "#open"
                ),
            ))
        return findings