"""
PPY004 — weakref.proxy() lifetime differs on PyPy due to GC model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, a weakref.proxy() to a dead object raises ReferenceError
only when the proxy is accessed. On PyPy, a proxy may remain valid
longer or become dead at a different point because PyPy's garbage
collector is not reference-count based. Code that assumes proxy death
coincides with reference count reaching zero may behave differently.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class WeakrefProxyRule(BaseRule):
    rule_id = "PPY004"
    title   = "weakref.proxy() lifetime differs on PyPy due to GC model"
    runtime = "pypy"

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
            is_proxy = False
            if isinstance(func, ast.Attribute):
                if func.attr == "proxy":
                    is_proxy = True
            elif isinstance(func, ast.Name) and func.id == "proxy":
                is_proxy = True

            if is_proxy:
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "weakref.proxy() lifetime can differ between "
                        "CPython and PyPy because PyPy's garbage collector "
                        "is not reference-count based. A proxy may remain "
                        "valid longer on PyPy, or become dead at a "
                        "different point than on CPython. Code that assumes "
                        "proxy death coincides with reference count "
                        "reaching zero may behave differently."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use weakref.ref() instead of weakref.proxy() — "
                        "call ref() to get the object and check for None explicitly. "
                        "This is safer on both CPython and PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                ))

        return findings