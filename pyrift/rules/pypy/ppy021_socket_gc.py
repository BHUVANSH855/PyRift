"""
PPY021 — Sockets not closed promptly on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, sockets are commonly closed promptly when their last strong
reference disappears because of reference counting. On PyPy, garbage
collection is tracing-based and object finalization can happen later.

This rule therefore flags socket creation when explicit lifecycle management
cannot be established statically.

The rule recognizes:

* ``with socket.socket() as s:``
* ``try/finally`` blocks that close the socket
* explicit ``s.close()`` calls in the same scope

It does not attempt interprocedural ownership analysis. A socket returned from
a function or passed to another function is therefore still considered
unmanaged unless an explicit close can be established locally.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class SocketGCRule(BaseRule):
    rule_id = "PPY021"
    title = "Socket not closed promptly on PyPy — GC timing"
    runtime = "pypy"
    severity = Severity.WARNING

    @staticmethod
    def _socket_call(node: ast.Call) -> bool:
        """Return True when *node* represents socket.socket() or socket()."""
        func = node.func

        if (
            isinstance(func, ast.Attribute)
            and func.attr == "socket"
            and isinstance(func.value, ast.Name)
            and func.value.id == "socket"
        ):
            return True

        return isinstance(func, ast.Name) and func.id == "socket"

    @staticmethod
    def _parent_map(tree: ast.AST) -> dict[int, ast.AST]:
        """Build a child -> parent map for *tree*."""
        parents: dict[int, ast.AST] = {}

        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[id(child)] = parent

        return parents

    @staticmethod
    def _is_in_context_manager(
        node: ast.Call,
        parent_map: dict[int, ast.AST],
    ) -> bool:
        """Return True if *node* is the context expression of a ``with``."""
        current = parent_map.get(id(node))

        while current is not None:
            if isinstance(current, ast.withitem):
                return current.context_expr is node

            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                break

            current = parent_map.get(id(current))

        return False

    @staticmethod
    def _containing_scope(
        node: ast.AST,
        parent_map: dict[int, ast.AST],
    ) -> ast.AST | None:
        """Return the nearest module/function scope containing *node*."""
        current = parent_map.get(id(node))

        while current is not None:
            if isinstance(
                current,
                (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                return current

            current = parent_map.get(id(current))

        return None

    @staticmethod
    def _assigned_names(
        socket_call: ast.Call,
        scope: ast.AST,
    ) -> set[str]:
        """Return simple names assigned from *socket_call* in *scope*."""
        names: set[str] = set()

        for node in ast.walk(scope):
            if isinstance(node, ast.Assign) and node.value is socket_call:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
                continue

            if (
                isinstance(node, (ast.AnnAssign, ast.NamedExpr))
                and node.value is socket_call
                and isinstance(node.target, ast.Name)
            ):
                names.add(node.target.id)

        return names

    @staticmethod
    def _has_direct_close(
        socket_call: ast.Call,
        scope: ast.AST,
    ) -> bool:
        """
        Return True when the socket variable is explicitly closed in *scope*.

        This recognizes direct attribute calls such as:

            s = socket.socket()
            s.close()

        regardless of whether the close is inside an ``if``, loop, or
        exception handler. The rule does not attempt to prove that every
        control-flow path reaches the close.
        """
        socket_names = SocketGCRule._assigned_names(socket_call, scope)

        if not socket_names:
            return False

        for node in ast.walk(scope):
            if not isinstance(node, ast.Call):
                continue

            func = node.func

            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "close"
                and isinstance(func.value, ast.Name)
                and func.value.id in socket_names
            ):
                continue

            # Do not count a close that occurs before the socket is created.
            if (
                hasattr(node, "lineno")
                and hasattr(socket_call, "lineno")
                and node.lineno < socket_call.lineno
            ):
                continue

            return True

        return False

    @staticmethod
    def _is_try_finally_closes_socket(
        socket_call: ast.Call,
        scope: ast.AST,
    ) -> bool:
        """Return True if a try/finally block closes the created socket."""
        socket_names = SocketGCRule._assigned_names(socket_call, scope)

        if not socket_names:
            return False

        socket_line = getattr(socket_call, "lineno", 0)

        for node in ast.walk(scope):
            if not isinstance(node, ast.Try):
                continue

            if not node.finalbody:
                continue

            if node.lineno <= socket_line:
                continue

            for final_node in node.finalbody:
                for child in ast.walk(final_node):
                    if not isinstance(child, ast.Call):
                        continue

                    func = child.func

                    if (
                        isinstance(func, ast.Attribute)
                        and func.attr == "close"
                        and isinstance(func.value, ast.Name)
                        and func.value.id in socket_names
                    ):
                        return True

        return False

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        parent_map = self._parent_map(node)
        findings: list[Finding] = []

        for socket_call in ast.walk(node):
            if not isinstance(socket_call, ast.Call):
                continue

            if not self._socket_call(socket_call):
                continue

            # Safe: socket is explicitly managed by a context manager.
            if self._is_in_context_manager(socket_call, parent_map):
                continue

            scope = self._containing_scope(socket_call, parent_map)

            if scope is not None:
                # Safe: explicit local close.
                if self._has_direct_close(socket_call, scope):
                    continue

                # Safe: try/finally explicitly closes the socket.
                if self._is_try_finally_closes_socket(socket_call, scope):
                    continue

            findings.append(
                Finding(
                    file=filename,
                    line=socket_call.lineno,
                    col=socket_call.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "A socket is created without an explicit local "
                        "cleanup path. On CPython, reference counting often "
                        "causes sockets to close promptly when their last "
                        "reference disappears. On PyPy, tracing garbage "
                        "collection can delay cleanup, potentially keeping "
                        "file descriptors open longer than expected."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Always manage sockets explicitly: prefer "
                        "'with socket.socket() as s:' or ensure the socket "
                        "is closed with 's.close()' in a guaranteed cleanup "
                        "path such as try/finally."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                )
            )

        return findings