"""
PPY046 — __debug__ is always True on PyPy regardless of -O flag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, running with -O (optimise) sets __debug__ to False,
which removes assert statements and code inside 'if __debug__:' blocks.
On PyPy, __debug__ is always True even when running with -O.
Code that uses __debug__ to gate expensive validation or debugging
code will run that code on PyPy even with optimisation flags.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class DebugConstantRule(BaseRule):
    rule_id = "PPY046"
    title   = "__debug__ is always True on PyPy — -O flag has no effect"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # Detect: if __debug__: ... or if not __debug__: ...
            if isinstance(n, ast.If):
                test = n.test
                is_debug_check = False
                if isinstance(test, ast.Name) and test.id == "__debug__" or (isinstance(test, ast.UnaryOp) and
                        isinstance(test.op, ast.Not) and
                        isinstance(test.operand, ast.Name) and
                        test.operand.id == "__debug__"):
                    is_debug_check = True
                if is_debug_check:
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "'if __debug__:' block detected. On CPython, "
                            "running with -O sets __debug__ to False, removing "
                            "this code. On PyPy, the -O flag behaviour with "
                            "__debug__ may differ — code gated on __debug__ "
                            "may not be removed even with optimisation flags. "
                            "Use an explicit environment variable instead of "
                            "__debug__ for conditional debug code."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Do not rely on -O to remove debug code on PyPy. "
                            "Use an explicit environment variable or config flag "
                            "instead: DEBUG = os.getenv('DEBUG', '0') == '1'"
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                            "#miscellaneous"
                        ),
                    ))
        return findings