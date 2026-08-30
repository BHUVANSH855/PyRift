"""
PPY052 — importlib.abc resource classes may differ on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyPy's implementation of importlib.abc may have subtle differences:
  - ResourceReader interface may have different method signatures
  - TraversableResources may return different types
  - Some abstract methods may be implemented differently

Code that subclasses importlib.abc resource classes or relies on
their exact interface may behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_RESOURCE_CLASSES = {"ResourceReader", "TraversableResources", "ResourceContents"}


class ImportlibAbcPyPyRule(BaseRule):
    rule_id = "PPY052"
    title   = "importlib.abc resource classes may differ on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        imp_map = collect_imports(node)

        for info in imp_map.by_statement():
            if info.module == "importlib.abc" and info.name in _RESOURCE_CLASSES:
                findings.append(Finding(
                            file=filename, line=info.line, col=info.col,
                            rule_id=self.rule_id, title=self.title,
                            description=(
                                f"importlib.abc.{info.name} may have subtle "
                                "differences on PyPy. The resource reader "
                                "interface may have different method signatures "
                                "or return types compared to CPython."
                            ),
                            severity=Severity.INFO,
                            runtime=Runtime.PYPY,
                            suggestion=(
                                f"Test any code using importlib.abc.{info.name} "
                                "on both CPython and PyPy to ensure compatibility."
                            ),
                            docs_url="https://doc.pypy.org/en/latest/cpython_differences.html",
                        ))

        # Also detect attribute access: importlib.abc.ResourceReader
        for n in ast.walk(node):
            if (isinstance(n, ast.Attribute)
                    and n.attr in _RESOURCE_CLASSES
                    and isinstance(n.value, ast.Attribute)
                    and n.value.attr == "abc"
                    and isinstance(n.value.value, ast.Name)
                    and n.value.value.id == "importlib"):
                findings.append(Finding(
                    file=filename, line=n.lineno, col=n.col_offset,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        f"importlib.abc.{n.attr} may have subtle "
                        "differences on PyPy."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Test on both CPython and PyPy."
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
