"""
PPY008 — threading.local() behaves differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, threading.local() data is immediately released when
a thread exits. On PyPy, due to the tracing GC, thread-local
storage may not be released until the GC runs — leaking memory
in long-running servers that create and destroy many threads.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ThreadingLocalRule(BaseRule):
    rule_id = "PPY008"
    title   = "threading.local() cleanup timing differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

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
                    func.attr == "local" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "threading"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "threading.local() data cleanup timing differs on PyPy. "
                        "On CPython, thread-local data is released immediately "
                        "when a thread exits (reference counting). On PyPy, "
                        "thread-local storage may persist until the next GC "
                        "cycle — causing memory leaks in servers that create "
                        "many short-lived threads."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Explicitly delete thread-local data before thread exit: "
                        "del local_obj.attribute "
                        "or use a try/finally block to clean up thread-local state."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                ))
        return findings