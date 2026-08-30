"""
PPY049 — GC behavior differences on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyPy uses a different garbage collection strategy than CPython:
  - PyPy uses a generational GC with different thresholds
  - gc.collect() may trigger different objects to be collected
  - gc.get_objects() returns different object counts
  - Weakref callbacks may fire at different times
  - gc.disable() has different effects on reference counting

Code that depends on deterministic GC timing or gc.collect() behavior
may behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class GcBehaviorRule(BaseRule):
    rule_id = "PPY049"
    title = "GC behavior differs between PyPy and CPython"
    runtime = "pypy"
    severity = Severity.WARNING

    _GC_FUNCTIONS = frozenset(
        {
            "collect",
            "get_objects",
            "get_count",
            "set_threshold",
            "get_referrers",
            "get_referents",
            "disable",
            "enable",
        }
    )

    @staticmethod
    def _gc_bindings(node: ast.AST) -> set[str]:
        """Return names that are definitely bound to the stdlib gc module."""
        bindings: set[str] = set()

        for current in ast.walk(node):
            if isinstance(current, ast.Import):
                for alias in current.names:
                    if alias.name == "gc":
                        bindings.add(alias.asname or "gc")

            elif isinstance(current, ast.ImportFrom):
                # ``from gc import collect`` binds the imported function, not
                # the gc module, so it must not make the local name a module
                # binding.
                continue

        return bindings

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        gc_bindings = self._gc_bindings(node)

        for current in ast.walk(node):
            if not isinstance(current, ast.Call):
                continue

            func = current.func

            if (
                not isinstance(func, ast.Attribute)
                or not isinstance(func.value, ast.Name)
                or func.value.id not in gc_bindings
                or func.attr not in self._GC_FUNCTIONS
            ):
                continue

            if func.attr in {"disable", "enable"}:
                description = (
                    f"gc.{func.attr}() has different effects on PyPy. "
                    "PyPy's GC is less dependent on reference counting, "
                    "so disabling GC may not prevent collection as "
                    "expected."
                )
                suggestion = (
                    "Avoid relying on gc.disable()/enable() for "
                    "controlling object lifetime. Use weak references "
                    "or explicit cleanup patterns instead."
                )
            else:
                description = (
                    f"gc.{func.attr}() behaves differently on PyPy. "
                    "PyPy uses a generational GC with different "
                    "thresholds and collection strategies. "
                    "gc.collect() may trigger different objects to "
                    "be collected, and gc.get_objects() returns "
                    "different counts."
                )
                suggestion = (
                    "Do not rely on deterministic GC timing or exact "
                    "gc.get_objects() counts. For memory management, "
                    "use context managers and explicit cleanup instead."
                )

            findings.append(
                Finding(
                    file=filename,
                    line=current.lineno,
                    col=current.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=description,
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=suggestion,
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                    ),
                )
            )

        return findings
