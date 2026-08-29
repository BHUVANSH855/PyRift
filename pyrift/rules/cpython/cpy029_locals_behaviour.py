"""
CPY029 — locals() behaviour changed in Python 3.13 (PEP 667)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before Python 3.13, modifying the dict returned by locals() had
undefined behaviour — changes might or might not affect local
variables. In Python 3.13 (PEP 667), locals() now has defined
semantics: the returned mapping is a snapshot and modifying it
never affects the actual local variables.

Only flag when the locals() return value is stored in a variable
(indicating likely mutation intent), not when used directly in
expressions like print(locals()) or logging.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


def _is_locals_call(n: ast.AST) -> bool:
    return (
        isinstance(n, ast.Call) and
        isinstance(n.func, ast.Name) and
        n.func.id == "locals" and
        not n.args and not n.keywords
    )


class LocalsBehaviourRule(BaseRule):
    rule_id = "CPY029"
    title   = "locals() semantics changed in Python 3.13 (PEP 667)"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Flag: d = locals() — storing implies likely mutation
            if isinstance(n, ast.Assign) and _is_locals_call(n.value):
                findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "The result of locals() is stored in a variable. "
                            "Before Python 3.13, modifying the dict returned "
                            "by locals() had undefined behaviour — changes "
                            "sometimes affected local variables. "
                            "In Python 3.13 (PEP 667), locals() returns a "
                            "snapshot — modifying it never affects actual "
                            "local variables. Code relying on locals() "
                            "mutation will silently break on 3.13+."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.13",
                        suggestion=(
                            "Do not modify the dict returned by locals(). "
                            "Use explicit variable assignment instead. "
                            "If you need dynamic variable access, use a "
                            "regular dict."
                        ),
                        docs_url="https://peps.python.org/pep-0667/",
                    ))

        return findings