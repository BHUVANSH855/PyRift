"""
PPY039 — os.fork() not available on all PyPy platforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
os.fork() is only available on Unix-like systems. On PyPy,
os.fork() may work on Linux but is not supported on all
platforms PyPy runs on. Additionally, forking a PyPy process
with JIT-compiled code can cause issues with the JIT state
not being properly reset in the child process.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class OsForkRule(BaseRule):
    rule_id = "PPY039"
    title   = "os.fork() may not work correctly on all PyPy platforms"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "fork" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "os"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "os.fork() is called here. "
                        "On PyPy, forking a process with active "
                        "JIT-compiled code can cause issues — the JIT state "
                        "may not be properly reset in the child process. "
                        "This is an observed compatibility concern; use "
                        "multiprocessing with the spawn start method as a "
                        "safer cross-platform alternative."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use multiprocessing with spawn or forkserver "
                        "start methods instead of os.fork() directly. "
                        "These are safer on both CPython and PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                    ),
                ))
        return findings