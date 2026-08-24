"""
PPY015 — Pending generator cleanup timing differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A generator left pending in the middle is garbage-collected later
in PyPy than in CPython. If the yield is inside a try: or with:
block, the finally/cleanup may run much later than expected on PyPy,
silently leaking resources.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class GeneratorGCRule(BaseRule):
    rule_id = "PPY015"
    title   = "Generator cleanup timing differs on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.FunctionDef):
                continue

            # Check if this is a generator (contains yield)
            has_yield = any(
                isinstance(child, (ast.Yield, ast.YieldFrom))
                for child in ast.walk(n)
            )
            if not has_yield:
                continue

            # Check if yield is inside try or with block
            for child in ast.walk(n):
                if isinstance(child, (ast.Try, ast.With)):
                    inner_yield = any(
                        isinstance(c, (ast.Yield, ast.YieldFrom))
                        for c in ast.walk(child)
                    )
                    if inner_yield:
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                f"Generator '{n.name}' yields inside a "
                                "try/with block. On CPython, if a generator "
                                "is abandoned mid-execution, the finally/cleanup "
                                "runs promptly via reference counting. On PyPy, "
                                "the generator is GC'd later — finally blocks "
                                "and context manager __exit__ may run much later "
                                "or at unpredictable times, silently leaking "
                                "resources."
                            ),
                            severity=Severity.WARNING,
                            runtime=Runtime.PYPY,
                            suggestion=(
                                "Always fully exhaust generators or use "
                                "explicit close(): gen.close(). "
                                "Use try/finally in the caller to guarantee "
                                "cleanup rather than relying on generator GC."
                            ),
                            docs_url=(
                                "https://doc.pypy.org/en/latest/cpython_differences.html"
                                "#differences-related-to-garbage-collection-strategies"
                            ),
                        ))
                        break

        return findings