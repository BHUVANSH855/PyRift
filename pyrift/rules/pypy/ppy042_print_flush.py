"""
PPY042 — print() with flush=True behaves differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, print(flush=True) immediately flushes the output buffer.
On PyPy, the flush may be delayed due to buffering differences,
especially when writing to pipes or redirected stdout. This can
cause output to appear out of order or be lost on crash.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class PrintFlushRule(BaseRule):
    rule_id = "PPY042"
    title   = "print(flush=True) may not flush immediately on PyPy"
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
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not (isinstance(func, ast.Name) and func.id == "print"):
                continue
            for kw in n.keywords:
                if (
                    kw.arg == "flush"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value
                ):
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                "print(flush=True) is called. "
                                "For output that must appear immediately — "
                                "especially to pipes or redirected stdout — "
                                "follow with an explicit sys.stdout.flush() call. "
                                "This is a best practice on all runtimes and "
                                "avoids relying on buffering implementation details."
                            ),
                            severity=Severity.INFO,
                            runtime=Runtime.PYPY,
                            suggestion=(
                                "For critical output that must appear immediately "
                                "on PyPy, use sys.stdout.flush() explicitly after "
                                "print(), or set PYTHONUNBUFFERED=1 in the "
                                "environment before running on PyPy."
                            ),
                            docs_url=(
                                "https://doc.pypy.org/en/latest/"
                                "cpython_differences.html"
                            ),
                        ))
        return findings