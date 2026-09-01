"""
PPY005 — File buffering behaviour differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Warn about writable files where lifecycle management is not explicit.

Writable files should have an explicit lifecycle on PyPy. A context manager
is preferred, but an explicit ``close()`` is also considered sufficient when
the opened file object is assigned to a local variable and that variable is
closed later in the same scope.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class IoBufferingRule(BaseRule):
    rule_id = "PPY005"
    title = "File write without explicit lifecycle management on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    WRITE_FLAGS = frozenset({"w", "a", "x", "+"})
    OPEN_NAMES = frozenset({"open"})
    OPEN_MODULES = frozenset({"io", "builtins"})

    @classmethod
    def _is_write_mode(cls, mode: str) -> bool:
        """Return whether an ``open()`` mode can write to the file."""
        return any(flag in mode for flag in cls.WRITE_FLAGS)

    @classmethod
    def _is_open_call(cls, node: ast.Call) -> bool:
        """Return whether *node* is a supported ``open()`` call."""
        func = node.func

        if isinstance(func, ast.Name):
            return func.id in cls.OPEN_NAMES

        return (
            isinstance(func, ast.Attribute)
            and func.attr == "open"
            and isinstance(func.value, ast.Name)
            and func.value.id in cls.OPEN_MODULES
        )

    @classmethod
    def _is_write_open(cls, node: ast.Call) -> bool:
        """Return whether *node* opens a file in a writable mode."""
        if not cls._is_open_call(node):
            return False

        if len(node.args) >= 2:
            mode = node.args[1]
            if (
                isinstance(mode, ast.Constant)
                and isinstance(mode.value, str)
            ):
                return cls._is_write_mode(mode.value)

        for keyword in node.keywords:
            if (
                keyword.arg == "mode"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                return cls._is_write_mode(keyword.value.value)

        return False

    @staticmethod
    def _build_parent_map(node: ast.AST) -> dict[int, ast.AST]:
        """Build a child-to-parent AST mapping."""
        parent_map: dict[int, ast.AST] = {}

        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                parent_map[id(child)] = parent

        return parent_map

    @staticmethod
    def _is_context_manager_call(
        node: ast.Call,
        parent_map: dict[int, ast.AST],
    ) -> bool:
        """Return whether *node* is directly used as a ``with`` context."""
        current = parent_map.get(id(node))

        while current is not None:
            if isinstance(current, ast.withitem):
                return current.context_expr is node

            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                break

            current = parent_map.get(id(current))

        return False

    @staticmethod
    def _assigned_names(
        open_call: ast.Call,
        tree: ast.AST,
    ) -> set[str]:
        """Return names assigned the value produced by *open_call*."""
        names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and node.value is open_call:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)

            elif (
                isinstance(node, ast.AnnAssign)
                and node.value is open_call
                and isinstance(node.target, ast.Name)
            ) or (
                isinstance(node, ast.NamedExpr)
                and node.value is open_call
                and isinstance(node.target, ast.Name)
            ):
                names.add(node.target.id)

        return names

    @staticmethod
    def _same_scope(
        node: ast.AST,
        scope: ast.AST,
        parent_map: dict[int, ast.AST],
    ) -> bool:
        """Return whether *node* belongs directly to *scope*."""
        current = parent_map.get(id(node))

        while current is not None:
            if current is scope:
                return True

            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return False

            current = parent_map.get(id(current))

        return False

    @staticmethod
    def _is_close_call_for_names(
        node: ast.AST,
        names: set[str],
        open_call: ast.Call,
    ) -> bool:
        """Return whether *node* closes one of the opened file variables."""
        if not isinstance(node, ast.Call):
            return False

        func = node.func

        if not isinstance(func, ast.Attribute):
            return False

        if func.attr != "close":
            return False

        if not isinstance(func.value, ast.Name):
            return False

        if func.value.id not in names:
            return False

        return not (
            hasattr(node, "lineno")
            and hasattr(open_call, "lineno")
            and node.lineno < open_call.lineno
        )

    @classmethod
    def _has_explicit_close(
        cls,
        open_call: ast.Call,
        tree: ast.AST,
        parent_map: dict[int, ast.AST],
    ) -> bool:
        """
        Return whether the opened file is explicitly closed later.

        Only accept a close in the same function/module scope. This avoids
        treating an unrelated ``close()`` in another nested function as proof
        that the file lifecycle is managed.
        """
        names = cls._assigned_names(open_call, tree)

        if not names:
            return False

        scope: ast.AST | None = None
        current = parent_map.get(id(open_call))

        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scope = current
                break

            if isinstance(current, ast.Module):
                scope = current
                break

            current = parent_map.get(id(current))

        if scope is None:
            return False

        for candidate in ast.walk(scope):
            if candidate is open_call:
                continue

            if not cls._same_scope(candidate, scope, parent_map):
                continue

            if cls._is_close_call_for_names(
                candidate,
                names,
                open_call,
            ):
                return True

        return False

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        parent_map = self._build_parent_map(node)
        findings: list[Finding] = []

        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue

            if not self._is_write_open(call):
                continue

            if self._is_context_manager_call(call, parent_map):
                continue

            if self._has_explicit_close(call, node, parent_map):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=call.lineno,
                    col=call.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "A file is opened for writing without an explicit "
                        "lifecycle. PyPy's garbage collection and buffering "
                        "behaviour can differ from CPython, so relying on "
                        "implicit cleanup is less predictable."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Prefer 'with open(...) as f:' for deterministic "
                        "lifecycle management, or explicitly call "
                        "'f.close()' when a context manager is not suitable."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                )
            )

        return findings