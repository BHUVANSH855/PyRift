"""
CPY081 -- sys.last_type / sys.last_value / sys.last_traceback deprecated (3.12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``sys.last_type``, ``sys.last_value``, and ``sys.last_traceback`` were
deprecated in Python 3.12. Use ``sys.last_exc`` instead.

    sys.last_type        # deprecated 3.12
    sys.last_value       # deprecated 3.12
    sys.last_traceback   # deprecated 3.12
    sys.last_exc         # correct (available 3.12+)
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_DEPRECATED = frozenset({"last_type", "last_value", "last_traceback"})


class SysLastExcRule(BaseRule):
    rule_id = "CPY081"
    title = "sys.last_type/value/traceback deprecated (3.12), use sys.last_exc"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Attribute):
                continue
            if n.attr not in _DEPRECATED:
                continue
            if not (isinstance(n.value, ast.Name) and n.value.id == "sys"):
                continue
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"'sys.{n.attr}' was deprecated in Python 3.12. "
                    "Use 'sys.last_exc' which holds the exception "
                    "instance directly."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.12",
                suggestion=(
                    "Replace with sys.last_exc. If you need the "
                    "traceback, use sys.last_exc.__traceback__; "
                    "for the type, type(sys.last_exc)."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/sys.html"
                    "#sys.last_exc"
                ),
            ))
        return findings