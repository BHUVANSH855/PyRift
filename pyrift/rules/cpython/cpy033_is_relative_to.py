"""
CPY033 — pathlib.Path.is_relative_to requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pathlib.Path.is_relative_to() was added in Python 3.9.
Calling it on Python 3.8 or below raises AttributeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class IsRelativeToRule(BaseRule):
    rule_id = "CPY033"
    title   = "pathlib.Path.is_relative_to() requires Python 3.9+"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "is_relative_to"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "pathlib.Path.is_relative_to() was added in "
                        "Python 3.9. Calling it on Python 3.8 or below "
                        "raises AttributeError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.8",
                    suggestion=(
                        "For Python 3.8 compatibility use: "
                        "try: path.relative_to(base); return True "
                        "except ValueError: return False"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/pathlib.html"
                        "#pathlib.PurePath.is_relative_to"
                    ),
                ))
        return findings