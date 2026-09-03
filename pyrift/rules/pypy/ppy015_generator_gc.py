"""
PPY015 — Pending generator cleanup timing differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A generator left pending in the middle is garbage-collected later
in PyPy than in CPython. If the yield is inside a ``try/finally`` or
``with`` block, cleanup may run much later than expected on PyPy.

This rule intentionally focuses on cleanup-sensitive generator usage.
Generic ``try/except`` blocks are not reported because they do not
necessarily imply resource cleanup tied to generator finalization.

Nested function, async-function, class, and lambda scopes are treated
independently so a nested generator cannot be attributed to its parent.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class GeneratorGCRule(BaseRule):
    rule_id = "PPY015"
    title = "Generator cleanup timing differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    @staticmethod
    def _contains_yield(node: ast.AST) -> bool:
        """Return True when *node* contains yield/yield-from in this scope."""
        stack = [node]

        while stack:
            current = stack.pop()

            if isinstance(current, (ast.Yield, ast.YieldFrom)):
                return True

            if isinstance(
                current,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                ),
            ):
                continue

            stack.extend(ast.iter_child_nodes(current))

        return False

    @classmethod
    def _is_generator(cls, function: ast.FunctionDef) -> bool:
        """Return True when this function directly contains yield/yield-from."""
        for statement in function.body:
            if cls._contains_yield(statement):
                return True

        return False

    @staticmethod
    def _iter_function_scopes(node: ast.AST) -> list[ast.FunctionDef]:
        """Return all ordinary function scopes in the AST."""
        return [
            current
            for current in ast.walk(node)
            if isinstance(current, ast.FunctionDef)
        ]

    @staticmethod
    def _iter_cleanup_blocks(
        function: ast.FunctionDef,
    ) -> list[ast.AST]:
        """
        Return cleanup-sensitive try/with blocks in this function.

        Nested function, async-function, class, and lambda scopes are
        excluded so their control flow is not attributed to this function.
        """
        blocks: list[ast.AST] = []

        def visit(current: ast.AST) -> None:
            if isinstance(
                current,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                ),
            ):
                return

            if isinstance(current, ast.With):
                blocks.append(current)

            elif isinstance(current, ast.Try) and current.finalbody:
                # Only try/finally is cleanup-sensitive for this rule.
                blocks.append(current)

            for child in ast.iter_child_nodes(current):
                visit(child)

        for statement in function.body:
            visit(statement)

        return blocks

    @staticmethod
    def _block_contains_yield(block: ast.AST) -> bool:
        """
        Return True when the cleanup block directly contains a yield.

        Nested function, async-function, class, and lambda scopes are
        excluded.
        """
        stack = [block]

        while stack:
            current = stack.pop()

            if isinstance(current, (ast.Yield, ast.YieldFrom)):
                return True

            if isinstance(
                current,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                ),
            ):
                continue

            stack.extend(ast.iter_child_nodes(current))

        return False

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for function in self._iter_function_scopes(node):
            if not self._is_generator(function):
                continue

            cleanup_blocks = self._iter_cleanup_blocks(function)

            if not any(
                self._block_contains_yield(block)
                for block in cleanup_blocks
            ):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=function.lineno,
                    col=function.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"Generator '{function.name}' yields inside a "
                        "try/finally or with block. If the generator is "
                        "abandoned mid-execution, cleanup tied to its "
                        "finalization may occur later on PyPy than on "
                        "CPython. Resource cleanup should therefore not "
                        "depend on generator garbage collection timing."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Explicitly close or fully exhaust the generator "
                        "when cleanup timing matters. Do not rely on "
                        "generator garbage collection for deterministic "
                        "resource cleanup."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                )
            )

        return findings