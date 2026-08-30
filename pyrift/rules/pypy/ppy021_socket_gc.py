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
from pyrift.targets import TargetConfig


class SocketGCRule(BaseRule):
    rule_id = "PPY021"
    title   = "Socket not closed promptly on PyPy — GC timing"
    runtime = "pypy"
    severity = Severity.WARNING

    def _is_in_context_manager(self, node: ast.AST, tree: ast.AST) -> bool:
        """Return True if *node* is nested inside a ``with`` statement."""
        for parent in ast.walk(tree):
            if not isinstance(parent, ast.With):
                continue
            for item in parent.items:
                if item.context_expr is node:
                    return True
                for child in ast.walk(item.context_expr):
                    if child is node:
                        return True
        return False

    def _is_try_finally_closes_socket(self, node: ast.AST, tree: ast.AST) -> bool:
        """Return True if a try/finally block in the same scope closes the
        variable that the socket call was assigned to."""
        if not hasattr(node, 'lineno'):
            return False

        # Step 1: collect variable names assigned to this socket call
        socket_vars: set[str] = set()
        socket_line = node.lineno
        for assign in ast.walk(tree):
            if isinstance(assign, ast.Assign) and assign.value is node:
                for target in assign.targets:
                    if isinstance(target, ast.Name):
                        socket_vars.add(target.id)
                        socket_line = assign.lineno
        if not socket_vars:
            return False

        # Step 2: find a scope (Module / FunctionDef / AsyncFunctionDef) that
        # contains both the socket assignment and a try/finally closing it.
        def _is_descendant_of(tree_node: ast.AST, ancestor: ast.AST) -> bool:
            for child in ast.walk(ancestor):
                if child is tree_node:
                    return True
            return False

        for parent in ast.walk(tree):
            if not isinstance(parent, (ast.Module, ast.FunctionDef,
                                       ast.AsyncFunctionDef)):
                continue
            # Collect top-level statements in this scope
            stmts = getattr(parent, 'body', [])
            for stmt in stmts:
                if not isinstance(stmt, ast.Try):
                    continue
                if not stmt.finalbody:
                    continue
                # The try block must come after the socket assignment
                if stmt.lineno <= socket_line:
                    continue
                # Check if finally block closes a socket variable
                for fin in stmt.finalbody:
                    for fcall in ast.walk(fin):
                        if (isinstance(fcall, ast.Call) and
                                isinstance(fcall.func, ast.Attribute) and
                                fcall.func.attr == "close" and
                                isinstance(fcall.func.value, ast.Name) and
                                fcall.func.value.id in socket_vars):
                            return True
        return False

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
            is_socket = False
            if (isinstance(func, ast.Attribute) and
                    func.attr == "socket" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "socket") or (isinstance(func, ast.Name) and
                    func.id == "socket"):
                is_socket = True
            if not is_socket:
                continue
            # Exclusion: socket inside a `with` statement (context manager)
            if self._is_in_context_manager(n, node):
                continue
            # Exclusion: socket variable is closed in a try/finally block
            if self._is_try_finally_closes_socket(n, node):
                continue
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
