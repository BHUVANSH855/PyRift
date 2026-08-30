"""
CPY074 — code.__lnotab__ deprecated in Python 3.10 (PEP 626)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PEP 626 deprecated code.__lnotab__ in favor of code.co_lines() and
code.co_linetable(). The __lnotab__ attribute was based on an inaccurate
encoding that could not represent line number changes correctly.

Detects:
  code_obj.__lnotab__
  func.__lnotab__
  code.__lnotab__
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class CoLnotabDeprecatedRule(BaseRule):
    rule_id = "CPY074"
    title   = "code.__lnotab__ deprecated since Python 3.10 (PEP 626)"
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
            if isinstance(n, ast.Attribute) and n.attr == "__lnotab__":
                findings.append(Finding(
                    file=filename, line=n.lineno, col=n.col_offset,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        "code.__lnotab__ is deprecated since Python 3.10 "
                        "(PEP 626). It uses an inaccurate byte encoding that "
                        "cannot represent line number changes correctly."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.10",
                    suggestion=(
                        "Use code.co_lines() (returns iterator of "
                        "(start_line, end_line, bytecode_offset)) or "
                        "code.co_linetable() (returns line table bytes) instead."
                    ),
                    docs_url="https://peps.python.org/pep-0626/",
                ))
        return findings
