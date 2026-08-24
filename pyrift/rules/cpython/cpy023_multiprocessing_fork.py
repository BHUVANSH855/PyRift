"""
CPY023 — multiprocessing fork start method changing in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The default multiprocessing start method on Linux/BSD will change
from 'fork' to a safer method in Python 3.14. Code relying on the
default 'fork' behaviour may silently break.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class MultiprocessingForkRule(BaseRule):
    rule_id = "CPY023"
    title   = "multiprocessing default start method changing in Python 3.14"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Import):
                continue
            for alias in n.names:
                if alias.name == "multiprocessing":
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "The default multiprocessing start method on "
                            "Linux/BSD/POSIX is 'fork' in Python <= 3.13. "
                            "In Python 3.14 it will change to a safer method. "
                            "Code relying on fork semantics (shared memory, "
                            "inherited file descriptors) may silently break."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.14",
                        suggestion=(
                            "Explicitly set the start method: "
                            "multiprocessing.set_start_method('fork') "
                            "or use multiprocessing.get_context('fork') "
                            "to make the behaviour explicit and version-safe."
                        ),
                        docs_url=(
                            "https://docs.python.org/3/library/multiprocessing.html"
                            "#contexts-and-start-methods"
                        ),
                    ))
        return findings