"""
PPY010 — gc.collect() behaviour differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, gc.collect() triggers a full collection of cyclic
garbage. On PyPy, gc.collect() exists but behaves differently —
it may not collect all unreachable objects immediately, and the
number returned (objects collected) has different semantics.
Code that relies on gc.collect() for deterministic cleanup will
behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class GcCollectRule(BaseRule):
    rule_id = "PPY010"
    title   = "gc.collect() behaviour differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "collect" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "gc"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "gc.collect() on CPython triggers a full cyclic garbage "
                        "collection and returns the number of objects collected. "
                        "On PyPy, gc.collect() exists but uses a different GC "
                        "algorithm — the return value has different semantics and "
                        "cleanup is not guaranteed to be immediate. Code relying "
                        "on gc.collect() for deterministic resource release will "
                        "behave differently on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Do not rely on gc.collect() for deterministic cleanup. "
                        "Use context managers and explicit close() calls instead. "
                        "If testing memory behaviour, run tests on both runtimes."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                ))
        return findings