"""
PPY029 — Assigning to __builtins__ has no effect on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, assigning to __builtins__ in a module can change which
builtins are accessible. On PyPy, assigning to __builtins__ has
no effect — PyPy ignores it silently. Code that monkey-patches
builtins via __builtins__ assignment will silently fail on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class BuiltinsAssignRule(BaseRule):
    rule_id = "PPY029"
    title   = "Assigning to __builtins__ has no effect on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Assign):
                continue
            for target in n.targets:
                if (isinstance(target, ast.Name) and
                        target.id == "__builtins__"):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "Assigning to __builtins__ is used here. "
                            "On CPython, this can change which builtin "
                            "functions are accessible in a module. "
                            "On PyPy, assigning to __builtins__ is "
                            "silently ignored and has no effect."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Use the builtins module directly to modify "
                            "builtin behaviour: import builtins; "
                            "builtins.print = my_print. This works on "
                            "both CPython and PyPy."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                            "#miscellaneous"
                        ),
                    ))
        return findings