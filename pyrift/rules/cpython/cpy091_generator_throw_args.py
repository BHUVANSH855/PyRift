"""
CPY091 -- generator.throw() 3-argument form deprecated (3.12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In Python 3.12 the 3-argument form of ``generator.throw()`` was
deprecated.  The ``value`` and ``traceback`` positional arguments
after the exception type were already redundant because the same
information is carried by the exception instance itself.

    gen.throw(ExcType, exc_instance, tb)   # deprecated 3.12
    gen.throw(ExcType, "message")          # deprecated 3.12

Preferred:
    gen.throw(exc_instance)
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class GeneratorThrowArgsRule(BaseRule):
    rule_id = "CPY091"
    title = "generator.throw() 3-argument form deprecated in Python 3.12"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for call_node in ast.walk(node):
            if not isinstance(call_node, ast.Call):
                continue
            func = call_node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "throw"):
                continue
            # Flag when positional args >= 2 (type + value, or type + value + tb)
            # 1 positional arg (the exception instance) is the new correct form.
            positional = [
                a for a in call_node.args
                if not isinstance(a, ast.Starred)
            ]
            if len(positional) >= 2:
                findings.append(Finding(
                    file=filename,
                    line=call_node.lineno,
                    col=call_node.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The 3-argument form generator.throw(type, value, tb) "
                        "was deprecated in Python 3.12. Passing a separate "
                        "value or traceback alongside the exception type is "
                        "redundant — the exception instance already carries "
                        "that information."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        "Pass only the exception instance: "
                        "gen.throw(exc_instance). "
                        "Create the instance first if needed: "
                        "exc = ExcType('message'); gen.throw(exc)"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.12.html"
                        "#deprecated"
                    ),
                ))
        return findings