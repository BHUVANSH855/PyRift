"""
CPY096 -- threading.RLock() arbitrary positional/keyword arguments removed (3.15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The C implementation of ``threading.RLock`` previously accepted (and silently
discarded) arbitrary positional and keyword arguments for historical
compatibility reasons.  In Python 3.15 that tolerance is removed: passing any
arguments to ``threading.RLock()`` now raises ``TypeError``.

Deprecated since: 3.14
Removed in: 3.15

    threading.RLock()           # always correct
    threading.RLock(verbose=0)  # TypeError in 3.15
    threading.RLock(1, 2)       # TypeError in 3.15

Reference: https://docs.python.org/3/whatsnew/3.15.html#removed
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ThreadingRLockArgsRemovedRule(BaseRule):
    rule_id = "CPY096"
    title = "threading.RLock() with arguments raises TypeError in Python 3.15"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for call_info in collect_calls(node, "RLock", module="threading"):
            call = call_info.node
            if not call.args and not call.keywords:
                continue
            findings.append(Finding(
                file=filename,
                line=call_info.line,
                col=call_info.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "threading.RLock() accepted arbitrary arguments for "
                    "historical compatibility, but that tolerance was "
                    "deprecated in Python 3.14 and removed in 3.15. "
                    "Calling threading.RLock() with any arguments now "
                    "raises TypeError."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.15",
                suggestion="Call threading.RLock() with no arguments.",
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.15.html#removed"
                ),
                whatsnew_ref="3.15#removed",
            ))
        return findings
