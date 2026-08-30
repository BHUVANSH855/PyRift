"""
CPY069 — asyncio.iscoroutinefunction() deprecated in 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
asyncio.iscoroutinefunction() was deprecated in Python 3.14 in favor of
inspect.iscoroutinefunction(). The asyncio version was redundant and confusing
since it did not check for native coroutines properly.

Detects:
  asyncio.iscoroutinefunction(func)
  from asyncio import iscoroutinefunction
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class AsyncioIscoroutinefunctionRule(BaseRule):
    rule_id = "CPY069"
    title   = "asyncio.iscoroutinefunction() deprecated in Python 3.14"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # from asyncio import iscoroutinefunction
            if isinstance(n, ast.ImportFrom) and n.module == "asyncio":
                for alias in n.names:
                    if alias.name == "iscoroutinefunction":
                        findings.append(self._make(filename, n.lineno, n.col_offset))

            # asyncio.iscoroutinefunction(func)
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Attribute)
                        and func.attr == "iscoroutinefunction"
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "asyncio"):
                    findings.append(self._make(filename, n.lineno, n.col_offset))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename, line=line, col=col,
            rule_id=self.rule_id, title=self.title,
            description=(
                "asyncio.iscoroutinefunction() is deprecated since Python 3.14. "
                "Use inspect.iscoroutinefunction() instead, which correctly "
                "handles both native coroutines and generator-based coroutines."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Replace asyncio.iscoroutinefunction(func) with "
                "inspect.iscoroutinefunction(func)."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html",
        )
