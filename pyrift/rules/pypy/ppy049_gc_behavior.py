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

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        gc_functions = {
            "collect",
            "get_objects",
            "get_count",
            "set_threshold",
            "get_referrers",
            "get_referents",
        }

        for current in ast.walk(node):
            if not isinstance(current, ast.Call):
                continue

            func = current.func

            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "gc"
                and func.attr in gc_functions
            ):
                findings.append(
                    Finding(
                        file=filename,
                        line=current.lineno,
                        col=current.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"gc.{func.attr}() behaves differently on PyPy. "
                            "PyPy uses a generational GC with different "
                            "thresholds and collection strategies. "
                            "gc.collect() may trigger different objects to "
                            "be collected, and gc.get_objects() returns "
                            "different counts."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Do not rely on deterministic GC timing or exact "
                            "gc.get_objects() counts. For memory management, "
                            "use context managers and explicit cleanup instead."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/"
                            "cpython_differences.html"
                        ),
                    )
                )
                continue

            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "gc"
                and func.attr in {"disable", "enable"}
            ):
                findings.append(
                    Finding(
                        file=filename,
                        line=current.lineno,
                        col=current.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"gc.{func.attr}() has different effects on PyPy. "
                            "PyPy's GC is less dependent on reference counting, "
                            "so disabling GC may not prevent collection as "
                            "expected."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Avoid relying on gc.disable()/enable() for "
                            "controlling object lifetime. Use weak references "
                            "or explicit cleanup patterns instead."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/"
                            "cpython_differences.html"
                        ),
                    )
                )

        return findings
