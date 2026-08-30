"""
PPY053 — functools.lru_cache thread safety differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyPy's functools.lru_cache implementation has different thread safety
characteristics than CPython's:
  - PyPy uses a different locking strategy for the cache
  - The cache may not be thread-safe in the same way as CPython
  - maxsize enforcement may differ under concurrent access
  - cache_info() may report different values under contention

Code that relies on CPython's specific lru_cache thread safety guarantees
may behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class LruCacheThreadSafetyRule(BaseRule):
    rule_id = "PPY053"
    title   = "functools.lru_cache thread safety differs on PyPy"
    runtime = "pypy"

    def _is_lru_cache(self, node: ast.expr) -> bool:
        """Return True if the node represents functools.lru_cache or lru_cache."""
        # @functools.lru_cache (no parens) — Attribute node in decorator_list
        if (isinstance(node, ast.Attribute)
                and node.attr == "lru_cache"
                and isinstance(node.value, ast.Name)
                and node.value.id == "functools"):
            return True
        # @lru_cache (no parens) — Name node in decorator_list
        if isinstance(node, ast.Name) and node.id == "lru_cache":
            return True
        # functools.lru_cache() or lru_cache() — Call node
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "lru_cache":
                return True
            if (isinstance(func, ast.Attribute)
                    and func.attr == "lru_cache"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "functools"):
                return True
        return False

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # Check decorator lists on functions
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for deco in n.decorator_list:
                    if self._is_lru_cache(deco):
                        findings.append(Finding(
                            file=filename, line=deco.lineno, col=deco.col_offset,
                            rule_id=self.rule_id, title=self.title,
                            description=(
                                "functools.lru_cache has different thread safety "
                                "characteristics on PyPy. PyPy uses a different "
                                "locking strategy and cache implementation that "
                                "may not provide the same guarantees as CPython."
                            ),
                            severity=Severity.INFO,
                            runtime=Runtime.PYPY,
                            suggestion=(
                                "For thread-safe caching on PyPy, consider using "
                                "a custom cache implementation or threading locks "
                                "around cache access if needed."
                            ),
                            docs_url="https://doc.pypy.org/en/latest/cpython_differences.html",
                        ))

            # Also check standalone calls: functools.lru_cache(...)
            if isinstance(n, ast.Call) and self._is_lru_cache(n):
                findings.append(Finding(
                    file=filename, line=n.lineno, col=n.col_offset,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        "functools.lru_cache has different thread safety "
                        "characteristics on PyPy."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "For thread-safe caching on PyPy, consider using "
                        "a custom cache implementation or threading locks."
                    ),
                    docs_url="https://doc.pypy.org/en/latest/cpython_differences.html",
                ))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique
