"""
CPY006 — asyncio.timeout() requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
asyncio.timeout() and asyncio.timeout_at() were added in 3.11.
Using them on 3.10 raises AttributeError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

ASYNCIO_311 = {"timeout", "timeout_at", "TaskGroup"}


class AsyncioTimeoutRule(BaseRule):
    rule_id = "CPY006"
    title   = "asyncio.timeout() / TaskGroup requires Python 3.11+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if (
                isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id == "asyncio"
                and n.attr in ASYNCIO_311
            ):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"asyncio.{n.attr} was added in Python 3.11. "
                            "On Python 3.10 and below this raises AttributeError "
                            "at runtime."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.0",
                        affected_until="3.10",
                        suggestion=(
                            "Use asyncio.wait_for() for timeout handling on 3.10. "
                            "For TaskGroup, use anyio or asyncio.gather() instead."
                        ),
                        docs_url="https://docs.python.org/3/library/asyncio-task.html",
                    ))

        return findings