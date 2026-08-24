"""
CPY038 — asyncio.get_event_loop() raises RuntimeError in Python 3.12+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since Python 3.12, asyncio.get_event_loop() raises RuntimeError if
there is no current event loop and no loop has been set — it no longer
implicitly creates one. This silently worked before 3.12.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class AsyncioGetEventLoopRule(BaseRule):
    rule_id = "CPY038"
    title   = "asyncio.get_event_loop() raises RuntimeError in Python 3.12+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "get_event_loop" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "asyncio"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "asyncio.get_event_loop() silently created a new "
                        "event loop if none existed in Python <= 3.11. "
                        "Since Python 3.12, it raises RuntimeError if "
                        "there is no current event loop — the implicit "
                        "creation was removed. Code relying on this "
                        "implicit behaviour silently breaks on 3.12+."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        "Use asyncio.run() to run coroutines — it creates "
                        "and manages the event loop automatically. "
                        "Or use asyncio.get_event_loop_policy().get_event_loop() "
                        "if you need the loop directly."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/asyncio-eventloop.html"
                        "#asyncio.get_event_loop"
                    ),
                ))
        return findings