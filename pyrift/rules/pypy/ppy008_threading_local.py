"""
PPY008 — threading.local() cleanup timing differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Warn when thread-local state is created without explicit cleanup.

PyPy uses tracing garbage collection rather than CPython's reference
counting. Code that relies on thread-local objects becoming unreachable
at a particular point can therefore have different cleanup timing.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ThreadingLocalRule(BaseRule):
    rule_id = "PPY008"
    title = "threading.local() cleanup timing differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    @staticmethod
    def _is_threading_local(node: ast.Call) -> bool:
        """Return whether *node* is a threading.local() call."""
        func = node.func

        return (
            isinstance(func, ast.Attribute)
            and func.attr == "local"
            and isinstance(func.value, ast.Name)
            and func.value.id == "threading"
        )

    @staticmethod
    def _assigned_names(
        node: ast.AST,
        local_call: ast.Call,
    ) -> set[str]:
        """Return names assigned directly to the threading.local() result."""
        names: set[str] = set()

        for current in ast.walk(node):
            if isinstance(current, ast.Assign) and current.value is local_call:
                for target in current.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)

            elif (
                isinstance(current, (ast.AnnAssign, ast.NamedExpr))
                and current.value is local_call
                and isinstance(current.target, ast.Name)
            ):
                names.add(current.target.id)

        return names

    @staticmethod
    def _attribute_deleted(
        node: ast.AST,
        names: set[str],
        local_call: ast.Call,
    ) -> bool:
        """Return whether an attribute of the local object is explicitly deleted."""
        for current in ast.walk(node):
            if not isinstance(current, ast.Delete):
                continue

            for target in current.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in names
                ):
                    if (
                        hasattr(current, "lineno")
                        and hasattr(local_call, "lineno")
                        and current.lineno < local_call.lineno
                    ):
                        continue

                    return True

        return False

    @classmethod
    def _has_explicit_cleanup(
        cls,
        node: ast.AST,
        local_call: ast.Call,
    ) -> bool:
        """Return whether obvious explicit cleanup exists."""
        names = cls._assigned_names(node, local_call)

        if not names:
            return False

        return cls._attribute_deleted(node, names, local_call)

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue

            if not self._is_threading_local(call):
                continue

            if self._has_explicit_cleanup(node, call):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=call.lineno,
                    col=call.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "threading.local() state can have different cleanup "
                        "timing on PyPy because PyPy uses tracing garbage "
                        "collection rather than CPython's reference counting. "
                        "Relying on thread-local state becoming unreachable "
                        "at a particular point can therefore retain resources "
                        "longer than expected."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Explicitly clear thread-local attributes when they "
                        "are no longer needed, for example with "
                        "'del local_obj.attribute', or use a try/finally "
                        "block to guarantee cleanup."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                )
            )

        return findings