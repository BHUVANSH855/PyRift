"""
PPY033 — Exceptions in __del__ are ignored differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, if __del__ raises an exception, a warning is printed
to stderr and the exception is ignored. On PyPy, exceptions in
__del__ are also ignored but the warning may appear at a very
different time — sometimes long after the object was collected,
making debugging extremely difficult.

PyPy's own RPython implementation also contains explicitly marked
light finalizers and low-level cleanup destructors. Those runtime
internals should not be reported merely because they call a known
non-raising cleanup primitive.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class DelIgnoredExceptionsRule(BaseRule):
    rule_id = "PPY033"
    title = "Exceptions in __del__ appear at unpredictable times on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    _SAFE_CLEANUP_CALLS = frozenset(
        {
            "free",
            "free_raw_storage",
            "raw_free",
            "nullptr",
        }
    )

    @staticmethod
    def _has_light_finalizer_marker(node: ast.FunctionDef) -> bool:
        """Return whether a function is explicitly marked as a light finalizer.

        PyPy/RPython uses decorators such as::

            @rgc.must_be_light_finalizer

        to mark runtime-internal finalizers whose execution is subject to
        special GC/finalizer constraints.
        """
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Attribute)
                and decorator.attr == "must_be_light_finalizer"
            ):
                return True

            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "must_be_light_finalizer"
            ):
                return True

            if (
                isinstance(decorator, ast.Name)
                and decorator.id == "must_be_light_finalizer"
            ):
                return True

            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "must_be_light_finalizer"
            ):
                return True

        return False

    @classmethod
    def _is_known_cleanup_call(cls, node: ast.Call) -> bool:
        """Return whether *node* is a known low-level cleanup primitive."""
        func = node.func

        if isinstance(func, ast.Name):
            return func.id in cls._SAFE_CLEANUP_CALLS

        if isinstance(func, ast.Attribute):
            return func.attr in cls._SAFE_CLEANUP_CALLS

        return False

    @classmethod
    def _has_risky_code(cls, node: ast.FunctionDef) -> bool:
        """Return whether __del__ contains an explicit raise or risky call."""
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                return True

            if isinstance(child, ast.Call) and not cls._is_known_cleanup_call(
                child
            ):
                return True

        return False

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for current in ast.walk(node):
            if not isinstance(current, ast.FunctionDef):
                continue

            if current.name != "__del__":
                continue

            # PyPy's explicitly marked light finalizers are runtime-level
            # finalizers with special GC semantics. Do not report them as
            # ordinary application-level __del__ methods.
            if self._has_light_finalizer_marker(current):
                continue

            if not self._has_risky_code(current):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=current.lineno,
                    col=current.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "__del__ contains code that may raise exceptions. "
                        "On CPython, exceptions in __del__ produce a warning "
                        "to stderr immediately when the object is collected. "
                        "On PyPy, the warning may appear at a different time "
                        "because finalization is not reference-count based."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Wrap potentially-raising __del__ code in try/except "
                        "to prevent exceptions from escaping. Better: use "
                        "context managers or explicit cleanup methods instead "
                        "of relying on __del__."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                )
            )

        return findings