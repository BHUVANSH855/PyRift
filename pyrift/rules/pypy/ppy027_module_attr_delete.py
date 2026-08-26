"""
PPY027 — Deleting module/class attributes may be slower on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is a performance-oriented heuristic, so findings intentionally
use conservative confidence/evidence metadata.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class ModuleAttrDeleteRule(BaseRule):
    rule_id = "PPY027"
    title = "Deleting module/class attributes may be slower on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for current in ast.walk(node):
            if not isinstance(current, ast.Delete):
                continue

            for target in current.targets:
                if not isinstance(target, ast.Attribute):
                    continue

                findings.append(
                    Finding(
                        file=filename,
                        line=current.lineno,
                        col=current.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"Attribute '{target.attr}' is being deleted. "
                            "PyPy may handle repeated module/class "
                            "attribute deletion differently from CPython. "
                            "This is a performance heuristic rather than "
                            "proof of a hot-path regression."
                        ),
                        severity=Severity.INFO,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "If this deletion occurs in a hot path, benchmark the code "
                            "on both CPython and PyPy before relying on equivalent "
                            "performance. Otherwise, none is required."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/"
                            "cpython_differences.html#miscellaneous"
                        ),
                    )
                )

        return findings