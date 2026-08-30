"""
CPY065 — pkgutil.find_loader() / get_loader() removed in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pkgutil.find_loader() and pkgutil.get_loader() were deprecated in 3.12
(PEP 451) and removed in 3.14. They relied on importlib internals that
no longer exist.

Detects:
  pkgutil.find_loader('mod')
  pkgutil.get_loader('mod')
  from pkgutil import find_loader
  from pkgutil import get_loader
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED_FUNCS = {"find_loader", "get_loader"}


class PkgutilFindLoaderRule(BaseRule):
    rule_id = "CPY065"
    title   = "pkgutil.find_loader()/get_loader() removed in Python 3.14"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # from pkgutil import find_loader / get_loader
            if isinstance(n, ast.ImportFrom) and n.module == "pkgutil":
                for alias in n.names:
                    if alias.name in _REMOVED_FUNCS:
                        findings.append(self._make(filename, alias.name, n.lineno, n.col_offset))

            # pkgutil.find_loader(...) / pkgutil.get_loader(...)
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Attribute)
                        and func.attr in _REMOVED_FUNCS
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "pkgutil"):
                    findings.append(self._make(filename, func.attr, n.lineno, n.col_offset))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, func_name: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename,
            line=line,
            col=col,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                f"pkgutil.{func_name}() was deprecated in Python 3.12 (PEP 451) "
                "and removed in Python 3.14. It relied on deprecated importlib "
                "internals. Importing it on 3.14+ raises AttributeError."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Use importlib.util.find_spec() instead of pkgutil.find_loader(). "
                "For loader objects, use importlib.util.find_spec() and access "
                "spec.loader directly."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html",
        )
