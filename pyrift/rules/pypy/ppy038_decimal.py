"""
PPY038 — Decimal module uses different backend on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, the decimal module uses a fast C implementation.
On PyPy, it uses a pure Python/RPython implementation — slower
with potential rounding differences in edge cases.

Only flag when Decimal is used with non-default precision or
rounding context, where backend differences are most likely to
produce different results.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_CONTEXT_ATTRS = {
    "prec", "rounding", "Emin", "Emax", "capitals",
    "clamp", "traps", "flags",
}


class DecimalBackendRule(BaseRule):
    rule_id = "PPY038"
    title   = "decimal module uses different backend on PyPy"
    runtime = "pypy"
    severity = Severity.INFO

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Flag: getcontext().prec = N or localcontext() usage
            # These are the cases where backend precision differences matter
            if isinstance(n, ast.Call):
                func = n.func
                if isinstance(func, ast.Attribute) and func.attr in (
                    "getcontext", "localcontext", "setcontext"
                ):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "decimal context is being configured. CPython uses "
                            "a fast C implementation of decimal. PyPy uses a "
                            "pure Python/RPython implementation — slower with "
                            "potential rounding differences in edge cases when "
                            "using non-default precision or rounding modes."
                        ),
                        severity=Severity.INFO,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Test decimal-heavy code with non-default precision "
                            "on PyPy explicitly. Verify rounding behaviour "
                            "matches expectations on both CPython and PyPy "
                            "with your specific data."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                        ),
                    ))

        return findings