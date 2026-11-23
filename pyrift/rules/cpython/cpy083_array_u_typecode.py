"""
CPY083 -- array.array('u', ...) type code deprecated (3.13), removed (3.16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``'u'`` type code for ``array.array`` (Unicode character) was deprecated
in Python 3.3, emits a ``DeprecationWarning`` in 3.13, and is scheduled for
removal in Python 3.16. Use ``'w'`` (Py_UCS4) instead.

    array.array('u', "hello")   # deprecated 3.13, removed 3.16
    array.array('w', "hello")   # correct
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ArrayUTypecodeRule(BaseRule):
    rule_id = "CPY083"
    title = "array.array('u', ...) type code deprecated (3.13), use 'w'"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for call in collect_calls(node, "array", module="array"):
            if not call.args:
                continue
            first = call.args[0]
            if not (
                isinstance(first, ast.Constant)
                and first.value == "u"
            ):
                continue
            findings.append(Finding(
                file=filename,
                line=call.line,
                col=call.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "The 'u' type code for array.array (Py_UNICODE) "
                    "emits a DeprecationWarning in Python 3.13 and is "
                    "scheduled for removal in Python 3.16."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.13",
                affected_until="3.16",
                suggestion=(
                    "Replace 'u' with 'w' (Py_UCS4). The 'w' type code "
                    "stores 4-byte Unicode code points and is the "
                    "supported replacement."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/array.html"
                ),
            ))
        return findings