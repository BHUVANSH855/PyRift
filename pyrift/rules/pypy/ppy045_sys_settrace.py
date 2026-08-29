"""
PPY045 — sys.settrace() not fully supported on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, sys.settrace() installs a tracing function for every
executed line, call, and return — used by debuggers, profilers,
and coverage tools. On PyPy, sys.settrace() exists but disables
the JIT when active, causing massive performance degradation and
some tracing events may not fire at all.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class SysSettraceRule(BaseRule):
    rule_id = "PPY045"
    title   = "sys.settrace() disables JIT and is unreliable on PyPy"
    runtime = "pypy"

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
                    func.attr == "settrace" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "sys"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "sys.settrace() is called. On CPython, this installs "
                        "a tracing function for debugging and profiling. "
                        "On PyPy, sys.settrace() disables the JIT compiler "
                        "entirely — causing 10-100x performance degradation — "
                        "and some trace events may not fire correctly. "
                        "Coverage tools and debuggers using settrace will "
                        "silently give incomplete results on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "For profiling on PyPy, use vmprof instead of "
                        "settrace-based profilers. For coverage, use "
                        "coverage.py with PyPy-specific configuration. "
                        "Avoid settrace in production code on PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#miscellaneous"
                    ),
                ))
        return findings