"""
CPY029 — locals() behaviour changed in Python 3.13 (PEP 667)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before Python 3.13, modifying the dict returned by locals() had
undefined behaviour — changes might or might not affect local
variables. In Python 3.13 (PEP 667), locals() now has defined
semantics: the returned mapping is a snapshot and modifying it
never affects the actual local variables.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class LocalsBehaviourRule(BaseRule):
    rule_id = "CPY029"
    title   = "locals() semantics changed in Python 3.13 (PEP 667)"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not (isinstance(func, ast.Name) and func.id == "locals"):
                continue
            # Only flag when locals() result is used in an assignment
            # or subscript — indicating mutation attempt
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "locals() is called here. Before Python 3.13, "
                    "modifying the dict returned by locals() had undefined "
                    "behaviour — changes sometimes affected local variables. "
                    "In Python 3.13 (PEP 667), locals() returns a snapshot "
                    "and modifying it never affects actual local variables. "
                    "Code relying on locals() mutation will silently break."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.13",
                suggestion=(
                    "Do not modify the dict returned by locals(). "
                    "Use explicit variable assignment instead. "
                    "If you need dynamic variable access, use a regular dict."
                ),
                docs_url="https://peps.python.org/pep-0667/",
            ))

        return findings