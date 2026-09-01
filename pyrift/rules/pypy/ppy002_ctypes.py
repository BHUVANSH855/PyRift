"""
PPY002 — ctypes usage may differ on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Some ctypes functionality has different implementation characteristics
on PyPy. Code using ctypes APIs that depend on low-level pointers,
callbacks, structures, or native memory operations should be tested
explicitly on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

CTYPES_DANGEROUS = {
    "CDLL",
    "WinDLL",
    "OleDLL",
    "PyDLL",
    "CFUNCTYPE",
    "WINFUNCTYPE",
    "cast",
    "pointer",
    "byref",
    "Structure",
    "Union",
    "BitField",
    "memmove",
    "memset",
}


class CtypesRule(BaseRule):
    rule_id = "PPY002"
    title = "ctypes usage may differ on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    @staticmethod
    def _is_ctypes_attribute(node: ast.Attribute) -> bool:
        """Return whether *node* is ctypes.<dangerous API>."""
        return (
            node.attr in CTYPES_DANGEROUS
            and isinstance(node.value, ast.Name)
            and node.value.id == "ctypes"
        )

    @staticmethod
    def _collect_direct_imports(node: ast.AST) -> set[str]:
        """Collect names imported directly from ctypes."""
        names: set[str] = set()

        for current in ast.walk(node):
            if not isinstance(current, ast.ImportFrom):
                continue

            if current.module != "ctypes":
                continue

            for alias in current.names:
                if alias.name in CTYPES_DANGEROUS:
                    names.add(alias.asname or alias.name)

        return names

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        imp_map = collect_imports(node)
        ctypes_imported = imp_map.has_module("ctypes")
        direct_imports = self._collect_direct_imports(node)

        if not ctypes_imported and not direct_imports:
            return findings

        for current in ast.walk(node):
            if isinstance(current, ast.Attribute):
                if not self._is_ctypes_attribute(current):
                    continue

                findings.append(self._make_finding(filename, current))

            elif isinstance(current, ast.Call):
                if (
                    isinstance(current.func, ast.Name)
                    and current.func.id in direct_imports
                ):
                    findings.append(self._make_finding(filename, current))

        return findings

    def _make_finding(
        self,
        filename: str,
        node: ast.AST,
    ) -> Finding:
        return Finding(
            file=filename,
            line=node.lineno,  # type: ignore[attr-defined]
            col=node.col_offset,  # type: ignore[attr-defined]
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "A ctypes API with low-level native interaction is used. "
                "PyPy's ctypes implementation can differ from CPython, "
                "particularly for pointers, callbacks, structures, and "
                "native memory operations."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.PYPY,
            suggestion=(
                "Test this ctypes usage explicitly on PyPy. "
                "Consider cffi as a cross-runtime alternative when "
                "appropriate."
            ),
            docs_url="https://doc.pypy.org/en/latest/ctypes.html",
        )