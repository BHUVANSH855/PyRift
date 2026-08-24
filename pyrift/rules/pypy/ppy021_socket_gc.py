"""
PPY021 — Sockets not closed promptly on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, sockets are closed immediately when they go out of scope
due to reference counting. On PyPy, sockets (like files) are not
closed promptly — the OS limit on open file descriptors can be
reached silently before the GC runs.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class SocketGCRule(BaseRule):
    rule_id = "PPY021"
    title   = "Socket not closed promptly on PyPy — GC timing"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            is_socket = False
            if (isinstance(func, ast.Attribute) and
                    func.attr == "socket" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "socket") or (isinstance(func, ast.Name) and
                    func.id == "socket"):
                is_socket = True
            if is_socket:
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "A socket is created here. On CPython, sockets are "
                        "closed immediately when they go out of scope "
                        "(reference counting). On PyPy, sockets are closed "
                        "by the GC which may run much later — you can silently "
                        "exhaust the OS limit on open file descriptors in "
                        "long-running servers without any error until the limit "
                        "is hit."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Always use sockets as context managers: "
                        "'with socket.socket() as s:' to guarantee "
                        "prompt closure on both CPython and PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                ))
        return findings