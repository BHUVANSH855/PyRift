"""
CPY038 -- asyncio.get_event_loop() raises RuntimeError in Python 3.14+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since Python 3.14, asyncio.get_event_loop() raises RuntimeError if
there is no current event loop. Earlier Python versions could
implicitly create or obtain an event loop in cases where no current
loop had been set.
Code relying on implicit event-loop creation can therefore break
when running on Python 3.14+.
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class AsyncioGetEventLoopRule(BaseRule):
    rule_id = "CPY038"
    title = "asyncio.get_event_loop() raises RuntimeError in Python 3.14+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for call in collect_calls(node, "get_event_loop", module="asyncio"):
            findings.append(Finding(
                file=filename,
                line=call.line,
                col=call.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "asyncio.get_event_loop() raises RuntimeError "
                    "when no current event loop is set. Python 3.14 "
                    "changed this behavior so code that relied on "
                    "implicit event-loop creation can break on "
                    "Python 3.14+."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.14",
                suggestion=(
                    "Use asyncio.run() to run coroutines -- it "
                    "creates and manages the event loop "
                    "automatically. If you need direct event-loop "
                    "access, explicitly create or manage the "
                    "appropriate event loop."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/"
                    "asyncio-eventloop.html#asyncio.get_event_loop"
                ),
            ))

        return findings