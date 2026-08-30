"""
PPY051 — code.__lnotab__ / co_lnotab deprecated in PyPy too
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
While PEP 626 deprecated code.__lnotab__ in CPython 3.10, PyPy also
follows this deprecation. PyPy's implementation of code objects may
report different line number tables, and code.__lnotab__ may not be
available in future PyPy versions.

Detects:
  code_obj.__lnotab__
  func.__code__.__lnotab__
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class CoLnotabPyPyRule(BaseRule):
    rule_id = "PPY051"
    title   = "code.__lnotab__ deprecated on PyPy too"
    runtime = "pypy"

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
                        "code.__lnotab__ is deprecated and may not be "
                        "available in future PyPy versions. PyPy follows "
                        "CPython's PEP 626 deprecation of __lnotab__."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use code.co_lines() or code.co_linetable() instead "
                        "of __lnotab__ for line number information."
                    ),
                    docs_url="https://doc.pypy.org/en/latest/cpython_differences.html",
                ))
        return findings
