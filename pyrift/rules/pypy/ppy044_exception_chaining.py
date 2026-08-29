"""
PPY044 — Exception variable cleanup differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On CPython, when an exception is stored in a variable and the
except block exits, CPython explicitly deletes the variable to
break reference cycles (PEP 3110).

This rule reports cases where the exception variable is used after
the except block, because code relying on that variable remaining
available can behave differently across runtimes.

Using the exception variable normally inside the except block is
not reported.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ExceptionChainingRule(BaseRule):
    rule_id = "PPY044"
    title = "Exception variable cleanup timing differs on PyPy"
    runtime = "pypy"

    @staticmethod
    def _name_used_in_node(
        node: ast.AST,
        name: str,
    ) -> bool:
        """Return True when ``name`` is loaded somewhere in ``node``."""
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Name)
                and child.id == name
                and isinstance(child.ctx, ast.Load)
            ):
                return True

        return False

    @classmethod
    def _name_used_after_handler(
        cls,
        parent: ast.Try,
        handler: ast.ExceptHandler,
        name: str,
    ) -> bool:
        """
        Return True when the exception variable is read after the
        except handler has finished within the try statement.
        """
        handler_index = parent.handlers.index(handler)

        for later_handler in parent.handlers[handler_index + 1 :]:
            if any(
                cls._name_used_in_node(statement, name)
                for statement in later_handler.body
            ):
                return True

        for statement in parent.orelse:
            if cls._name_used_in_node(statement, name):
                return True

        for statement in parent.finalbody:
            if cls._name_used_in_node(statement, name):
                return True

        return False

    @staticmethod
    def _find_following_statements(
        statements: list[ast.stmt],
        target: ast.Try,
    ) -> list[ast.stmt]:
        """
        Return statements that occur after ``target`` in its containing
        statement list.

        Nested statement lists are searched recursively so a ``try``
        inside a function, loop, conditional, or other block is handled
        correctly.
        """
        for index, statement in enumerate(statements):
            if statement is target:
                return statements[index + 1 :]

            for child in ast.iter_child_nodes(statement):
                if isinstance(child, ast.stmt):
                    result = ExceptionChainingRule._find_following_statements(
                        [child],
                        target,
                    )
                    if result:
                        return result

        return []

    @classmethod
    def _name_used_after_try(
        cls,
        node: ast.AST,
        parent: ast.Try,
        name: str,
    ) -> bool:
        """
        Return True when ``name`` is read after the complete try
        statement in the containing statement block.
        """
        following = cls._find_following_statements(
            [node] if isinstance(node, ast.stmt) else list(getattr(node, "body", [])),
            parent,
        )

        return any(
            cls._name_used_in_node(statement, name)
            for statement in following
        )

    def _finding(
        self,
        handler: ast.ExceptHandler,
        name: str,
        filename: str,
    ) -> Finding:
        """Create the PPY044 finding for an exception variable."""
        return Finding(
            file=filename,
            line=handler.lineno,
            col=handler.col_offset,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                f"Exception variable '{name}' is used after the "
                "except handler exits. CPython explicitly clears "
                "exception variables at the end of an except handler "
                "to break reference cycles. Depending on exception-"
                "variable lifetime can therefore interact differently "
                "with PyPy's garbage collector."
            ),
            severity=Severity.INFO,
            runtime=Runtime.PYPY,
            suggestion=(
                f"If '{name}' must remain available after the except "
                "block, explicitly copy it to another variable inside "
                f"the handler, for example: saved_exc = {name}."
            ),
            docs_url=(
                "https://doc.pypy.org/en/latest/"
                "cpython_differences.html"
                "#differences-related-to-garbage-collection-strategies"
            ),
        )

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for parent in ast.walk(node):
            if not isinstance(parent, ast.Try):
                continue

            for handler in parent.handlers:
                if handler.name is None:
                    continue

                name = handler.name

                used_after_handler = self._name_used_after_handler(
                    parent,
                    handler,
                    name,
                )

                if not used_after_handler:
                    used_after_handler = self._name_used_after_try(
                        node,
                        parent,
                        name,
                    )

                if used_after_handler:
                    findings.append(
                        self._finding(
                            handler,
                            name,
                            filename,
                        )
                    )

        return findings