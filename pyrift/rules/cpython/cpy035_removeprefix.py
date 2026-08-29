"""
CPY035 — str.removeprefix / str.removesuffix require Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
str.removeprefix() and str.removesuffix() were added in Python 3.9
(PEP 616). Calling them on Python 3.8 or below raises AttributeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

STR_METHODS_39 = {"removeprefix", "removesuffix"}


class RemovePrefixRule(BaseRule):
    rule_id = "CPY035"
    title   = "str.removeprefix/removesuffix requires Python 3.9+"
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
                    func.attr in STR_METHODS_39):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"str.{func.attr}() was added in Python 3.9 "
                        "(PEP 616). Calling it on Python 3.8 or below "
                        "raises AttributeError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.8",
                    suggestion=(
                        "For Python 3.8 compatibility: "
                        "s[len(prefix):] if s.startswith(prefix) else s "
                        "(for removeprefix) or "
                        "s[:-len(suffix)] if s.endswith(suffix) else s "
                        "(for removesuffix)."
                    ),
                    docs_url="https://peps.python.org/pep-0616/",
                ))
        return findings