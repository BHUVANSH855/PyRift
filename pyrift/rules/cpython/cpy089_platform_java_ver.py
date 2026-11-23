"""
CPY089 -- platform.java_ver() removed (3.15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``platform.java_ver()`` was removed in Python 3.15. It was only relevant
when running CPython on Jython, which is no longer maintained.

    platform.java_ver()   # removed 3.15
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class PlatformJavaVerRule(BaseRule):
    rule_id = "CPY089"
    title = "platform.java_ver() removed in Python 3.15"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for call in collect_calls(node, "java_ver", module="platform"):
            findings.append(Finding(
                file=filename,
                line=call.line,
                col=call.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "platform.java_ver() was removed in Python 3.15. "
                    "It was only useful when running on Jython and "
                    "always returned empty strings on CPython."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.15",
                suggestion=(
                    "Remove the call. If you are checking whether the "
                    "runtime is Jython, use "
                    "platform.python_implementation() == 'Jython' "
                    "instead."
                ),
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.15.html"
                    "#removed"
                ),
            ))
        return findings