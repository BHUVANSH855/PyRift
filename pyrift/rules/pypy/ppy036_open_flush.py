"""
PPY036 — open() in text mode flushes differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, opening a file in text mode with line buffering
(buffering=1) causes the file to flush after every newline.
On PyPy, this buffering hint may be ignored and data may
sit in the buffer longer, causing silent data loss on crash.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class OpenFlushRule(BaseRule):
    rule_id = "PPY036"
    title   = "open() line buffering behaves differently on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not (isinstance(func, ast.Name) and func.id == "open"):
                continue
            # Check for buffering=1 (line buffering) keyword
            for kw in n.keywords:
                if (
                    kw.arg == "buffering"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value == 1
                ):
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                "open() is called with buffering=1 (line "
                                "buffering). On CPython, this causes the "
                                "file to flush after every newline in text "
                                "mode. On PyPy, this buffering hint may be "
                                "ignored — data may remain in the buffer "
                                "longer, silently losing writes on crash."
                            ),
                            severity=Severity.WARNING,
                            runtime=Runtime.PYPY,
                            suggestion=(
                                "Use explicit flush() calls after important "
                                "writes, or use a context manager with "
                                "buffering=0 for binary mode, rather than "
                                "relying on line buffering behaviour."
                            ),
                            docs_url=(
                                "https://doc.pypy.org/en/latest/"
                                "cpython_differences.html"
                            ),
                        ))
        return findings