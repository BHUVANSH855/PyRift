"""
PPY047 — ctypes.util.find_library() unreliable on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, ctypes.util.find_library() searches the system for
shared libraries by name. On PyPy, this function may return None
or wrong results even when the library exists, because PyPy's
ctypes implementation uses a different search strategy that
may not correctly locate libraries on all platforms.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class CtypesFindLibraryRule(BaseRule):
    rule_id = "PPY047"
    title   = "ctypes.util.find_library() unreliable on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            # Detect: find_library('ssl') — bare call after import
            if isinstance(func, ast.Name) and func.id == "find_library":
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "find_library() is called here. On CPython, "
                        "ctypes.util.find_library() searches the system "
                        "for shared libraries by name. On PyPy, the function "
                        "may return None or incorrect results even when the "
                        "library exists — PyPy's ctypes uses a different search "
                        "strategy that does not work correctly on all platforms."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use cffi instead of ctypes on PyPy — it is fully "
                        "supported and has reliable library discovery. "
                        "If you must use ctypes, hardcode the library path "
                        "or use an environment variable as a fallback."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                    ),
                ))
            # Detect: ctypes.util.find_library() attribute call
            elif (isinstance(func, ast.Attribute) and
                    func.attr == "find_library"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "ctypes.util.find_library() is called here. On PyPy, "
                        "this may return None or incorrect results even when "
                        "the library exists."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use cffi instead of ctypes on PyPy — it is fully "
                        "supported and has reliable library discovery."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                    ),
                ))
        return findings