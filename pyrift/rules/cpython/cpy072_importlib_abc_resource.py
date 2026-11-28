"""
CPY072 — importlib.abc resource reader classes deprecated 3.12, removed 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.12 deprecated three classes that had moved from importlib.abc to
importlib.resources.abc in 3.11:

  - importlib.abc.ResourceReader   (deprecated 3.12, removed 3.14)
  - importlib.abc.Traversable      (deprecated 3.12, removed 3.14)
  - importlib.abc.TraversableResources (deprecated 3.12, removed 3.14)

Using them from importlib.abc raises DeprecationWarning on 3.12–3.13 and
ImportError / AttributeError on 3.14+.

Replacement: importlib.resources.abc.<ClassName>  (available since 3.11)

Detects:
  from importlib.abc import ResourceReader   # and the other two
  importlib.abc.ResourceReader               # attribute-access form
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

# All three names were deprecated in 3.12 and removed in 3.14.
# "ResourceContents" is NOT a real CPython class — do not include it.
_REMOVED_CLASSES = frozenset({"ResourceReader", "Traversable", "TraversableResources"})


class ImportlibAbcResourceRule(BaseRule):
    rule_id = "CPY072"
    title   = "importlib.abc resource classes deprecated 3.12, removed 3.14"
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
            # from importlib.abc import ResourceReader
            if isinstance(n, ast.ImportFrom) and n.module == "importlib.abc":
                for alias in n.names:
                    if alias.name in _REMOVED_CLASSES:
                        findings.append(self._make(filename, alias.name, alias.lineno, alias.col_offset))

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
                "and removed in Python 3.14. "
                "It raises DeprecationWarning on 3.12–3.13 and "
                "ImportError/AttributeError on 3.14+. "
                "Use importlib.resources.abc instead (available since 3.11)."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.12",
            docs_url="https://docs.python.org/3/whatsnew/3.14.html#removed",
            suggestion=(
                f"Replace importlib.abc.{class_name} with "
                f"importlib.resources.abc.{class_name}."
            ),
        )
