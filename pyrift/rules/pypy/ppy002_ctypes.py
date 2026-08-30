"""
PPY002 -- ctypes usage on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ctypes on PyPy is partially implemented. Pointer arithmetic,
callbacks, and structures with bit fields may silently produce
wrong results or crash on PyPy while working on CPython.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

CTYPES_DANGEROUS = {
    "CDLL", "WinDLL", "OleDLL", "PyDLL",
    "CFUNCTYPE", "WINFUNCTYPE",
    "cast", "pointer", "byref",
    "Structure", "Union", "BitField",
    "memmove", "memset",
}


class CtypesRule(BaseRule):
    rule_id = "PPY002"
    title   = "ctypes usage may silently fail on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        imp_map = collect_imports(node)
        ctypes_imported = imp_map.has_module("ctypes")

        if not ctypes_imported:
            return findings

        for n in ast.walk(node):
            if isinstance(n, ast.Attribute) and n.attr in CTYPES_DANGEROUS:
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"ctypes.{n.attr} is used here. "
                        "PyPy's ctypes implementation is incomplete -- "
                        "pointer arithmetic, callbacks, and bit-field structures "
                        "may silently produce wrong results or segfault on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Test explicitly on PyPy if ctypes is required. "
                        "Consider cffi as a cross-runtime alternative -- "
                        "fully supported on both CPython and PyPy."
                    ),
                    docs_url="https://doc.pypy.org/en/latest/ctypes.html",
                ))

        return findings