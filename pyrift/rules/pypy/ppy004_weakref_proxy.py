"""
PPY004 — weakref.proxy() lifetime differs on PyPy due to GC model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, a weakref.proxy() to a dead object raises ReferenceError
only when the proxy is accessed. On PyPy, proxy lifetime can differ
because PyPy uses a tracing garbage collector rather than CPython's
reference-counting GC.

This rule detects actual weakref.proxy usage while avoiding unrelated
functions/methods named proxy().
"""

from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class WeakrefProxyRule(BaseRule):
    rule_id = "PPY004"
    title = "weakref.proxy() lifetime differs on PyPy due to GC model"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        imports = collect_imports(node)

        weakref_aliases: set[str] = set()
        proxy_aliases: set[str] = set()

        # Track:
        #   import weakref
        #   import weakref as wr
        #   from weakref import proxy
        #   from weakref import proxy as make_proxy
        for info in imports.imports:
            if info.module == "weakref":
                if info.name is None:
                    weakref_aliases.add(
                        info.alias or "weakref"
                    )
                elif info.name == "proxy":
                    proxy_aliases.add(
                        info.alias or "proxy"
                    )

        # Without an actual weakref import there is no reliable evidence
        # that proxy() refers to weakref.proxy().
        if not weakref_aliases and not proxy_aliases:
            return findings

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue

            func = n.func
            is_proxy = False

            # weakref.proxy(...)
            # wr.proxy(...) where `wr` is an alias for weakref.
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "proxy"
                and isinstance(func.value, ast.Name)
                and func.value.id in weakref_aliases
            ) or (
                isinstance(func, ast.Name)
                and func.id in proxy_aliases
            ):
                is_proxy = True

            if not is_proxy:
                continue

            findings.append(
                Finding(
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
                        "call ref() to get the object and check for None "
                        "explicitly. This is safer on both CPython and PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                )
            )

        return findings