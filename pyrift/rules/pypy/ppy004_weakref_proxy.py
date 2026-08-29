"""
PPY004 — weakref.proxy() raises ReferenceError differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, a weakref.proxy() to a dead object raises ReferenceError
only when the proxy is accessed. On PyPy, it may raise ReferenceError
at unpredictable times due to GC differences — even before the object
appears to be dead from CPython's perspective.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class WeakrefProxyRule(BaseRule):
    rule_id = "PPY004"
    title   = "weakref.proxy() behaviour differs on PyPy"
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
                        "weakref.proxy() can raise ReferenceError at "
                        "unpredictable points on PyPy due to its tracing GC — "
                        "not just when the proxied object is accessed after death "
                        "as on CPython. Code must catch ReferenceError at every "
                        "access point, not just at the final dereference."
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