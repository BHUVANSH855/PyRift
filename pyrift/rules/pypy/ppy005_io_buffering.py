"""
PPY005 — File buffering behaviour differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Warn about writable files where lifecycle management is not explicit.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class IoBufferingRule(BaseRule):
    rule_id = "PPY005"
    title = "File write without explicit lifecycle management on PyPy"
    runtime = "pypy"

    @staticmethod
    def _is_write_open(node: ast.Call) -> bool:
        func = node.func

        is_open = (
            isinstance(func, ast.Name)
            and func.id == "open"
        ) or (
            isinstance(func, ast.Attribute)
            and func.attr == "open"
            and isinstance(func.value, ast.Name)
            and func.value.id in {"io", "builtins"}
        )

        if not is_open:
            return False

        if len(node.args) >= 2:
            mode = node.args[1]
            if (
                isinstance(mode, ast.Constant)
                and isinstance(mode.value, str)
                and any(
                    flag in mode.value
                    for flag in ("w", "a", "x")
                )
            ):
                return True

        for keyword in node.keywords:
            if (
                keyword.arg == "mode"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
                and any(
                    flag in keyword.value.value
                    for flag in ("w", "a", "x")
                )
            ):
                return True

        return False

    @staticmethod
    def _is_context_manager_call(
        node: ast.Call,
        parent_map: dict[int, ast.AST],
    ) -> bool:
        current = parent_map.get(id(node))

        while current is not None:
            if isinstance(current, ast.withitem):
                return current.context_expr is node

            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                break

            current = parent_map.get(id(current))

        return False

    def check(
        self,
        node: ast.AST,
        filename: str,
    ) -> list[Finding]:
        parent_map: dict[int, ast.AST] = {}

        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                parent_map[id(child)] = parent

        findings: list[Finding] = []

        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue

            if not self._is_write_open(call):
                continue

            if self._is_context_manager_call(
                call,
                parent_map,
            ):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=call.lineno,
                    col=call.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "A file is opened for writing without a "
                        "context-manager lifecycle. PyPy's garbage "
                        "collection and buffering behaviour can differ "
                        "from CPython, so relying on implicit cleanup "
                        "is less predictable."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Prefer 'with open(...) as f:' so that the "
                        "file lifecycle is explicit and deterministic."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                )
            )

        return findings