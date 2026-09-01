"""
PPY001 — Relying on __del__ for resource cleanup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CPython uses reference counting — __del__ is often called promptly when an
object becomes unreachable. PyPy uses a tracing GC — finalization timing can
be substantially later.

Flag resource-cleanup operations performed from ``__del__`` because correctness
must not depend on when the garbage collector chooses to finalize the object.
"""
from __future__ import annotations

import ast
from typing import ClassVar

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class GcFinalizerRule(BaseRule):
    rule_id = "PPY001"
    title = "Relying on __del__ for resource cleanup breaks on PyPy"
    runtime = "pypy"
    severity = Severity.ERROR

    RESOURCE_PATTERNS: ClassVar[frozenset[str]] = frozenset(
        {
            "close",
            "flush",
            "release",
            "disconnect",
            "cleanup",
            "shutdown",
            "terminate",
        }
    )

    @classmethod
    def _resource_methods_in_del(
        cls,
        function: ast.FunctionDef,
    ) -> list[str]:
        """Return resource-cleanup method names called by ``__del__``."""
        methods: list[str] = []

        for child in ast.walk(function):
            if not isinstance(child, ast.Call):
                continue

            func = child.func

            if isinstance(func, ast.Attribute):
                method = func.attr
            elif isinstance(func, ast.Name):
                method = func.id
            else:
                continue

            if method in cls.RESOURCE_PATTERNS and method not in methods:
                methods.append(method)

        return methods

    @staticmethod
    def _is_dunder_del(function: ast.FunctionDef) -> bool:
        """Return whether *function* is a ``__del__`` method."""
        return function.name == "__del__"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for function in ast.walk(node):
            if not isinstance(function, ast.FunctionDef):
                continue

            if not self._is_dunder_del(function):
                continue

            methods = self._resource_methods_in_del(function)

            if not methods:
                continue

            method_text = ", ".join(
                f"'{method}()'" for method in methods
            )

            if len(methods) == 1:
                cleanup_description = (
                    f"__del__ calls {method_text} for resource cleanup."
                )
            else:
                cleanup_description = (
                    f"__del__ calls {method_text} for resource cleanup."
                )

            findings.append(
                Finding(
                    file=filename,
                    line=function.lineno,
                    col=function.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"{cleanup_description} Finalization timing is "
                        "garbage-collector dependent. On CPython, "
                        "__del__ is often called promptly when the object "
                        "becomes unreachable because of reference counting. "
                        "On PyPy, tracing GC can delay finalization, so "
                        "resource cleanup must not depend on __del__."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.PYPY,
                    affected_from="any",
                    suggestion=(
                        "Use an explicit lifecycle instead: prefer a "
                        "context manager ('with'), or close/release the "
                        "resource explicitly in normal control flow or "
                        "a try/finally block. Do not rely on __del__ for "
                        "resource-management correctness."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                )
            )

        return findings