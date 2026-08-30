"""
CPY072 — importlib.abc resource reader classes removed in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.14 removes the deprecated importlib.abc resource reader classes:
  - importlib.abc.ResourceReader
  - importlib.abc.TraversableResources
  - importlib.abc.ResourceContents
These were replaced by importlib.resources.abc in Python 3.12+.

Detects:
  from importlib.abc import ResourceReader
  importlib.abc.ResourceReader
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED_CLASSES = {"ResourceReader", "TraversableResources", "ResourceContents"}


class ImportlibAbcResourceRule(BaseRule):
    rule_id = "CPY072"
    title   = "importlib.abc resource classes removed in Python 3.14"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # from importlib.abc import ResourceReader
            if isinstance(n, ast.ImportFrom) and n.module == "importlib.abc":
                for alias in n.names:
                    if alias.name in _REMOVED_CLASSES:
                        findings.append(self._make(filename, alias.name, n.lineno, n.col_offset))

            # importlib.abc.ResourceReader (attribute access)
            if (isinstance(n, ast.Attribute)
                    and n.attr in _REMOVED_CLASSES
                    and isinstance(n.value, ast.Attribute)
                    and n.value.attr == "abc"
                    and isinstance(n.value.value, ast.Name)
                    and n.value.value.id == "importlib"):
                findings.append(self._make(filename, n.attr, n.lineno, n.col_offset))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, class_name: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename, line=line, col=col,
            rule_id=self.rule_id, title=self.title,
            description=(
                f"importlib.abc.{class_name} was deprecated in Python 3.12 "
                "and removed in Python 3.14. Use importlib.resources.abc instead."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                f"Replace importlib.abc.{class_name} with "
                f"importlib.resources.abc.{class_name}."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html",
        )
