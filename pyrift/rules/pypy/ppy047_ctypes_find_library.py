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
from pyrift.targets import TargetConfig


def _collect_ctypes_imports(node: ast.AST) -> tuple[set[str], set[str]]:
    """Return (find_library_names, ctypes_module_names) from imports.

    - find_library_names: direct names bound to ctypes.util.find_library
    - ctypes_module_names: names bound to the ctypes.util module itself
    """
    fl_names: set[str] = set()
    mod_names: set[str] = set()

    for n in ast.walk(node):
        if not isinstance(n, ast.Import):
            continue
        for alias in n.names:
            real = alias.asname or alias.name
            if alias.name == "ctypes.util":
                # `import ctypes.util` binds the root name "ctypes" locally
                root = alias.name.split(".")[0]
                mod_names.add(alias.asname or root)
            elif alias.name == "ctypes":
                mod_names.add(real)

    for n in ast.walk(node):
        if not isinstance(n, ast.ImportFrom):
            continue
        mod = n.module or ""
        if mod in ("ctypes.util", "ctypes"):
            for alias in n.names:
                real = alias.asname or alias.name
                if alias.name == "find_library":
                    fl_names.add(real)
                elif alias.name == "util":
                    mod_names.add(real)

    return fl_names, mod_names


class CtypesFindLibraryRule(BaseRule):
    rule_id = "PPY047"
    title   = "ctypes.util.find_library() unreliable on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        fl_names, mod_names = _collect_ctypes_imports(node)
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func

            # Bare find_library() — only flag when imported from ctypes
            if isinstance(func, ast.Name) and func.id in fl_names:
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

            # Attribute access: X.find_library() — only flag when X is ctypes.util
            # Handles both util.find_library() and ctypes.util.find_library()
            elif isinstance(func, ast.Attribute) and func.attr == "find_library":
                is_ctypes = False
                val = func.value
                # Direct: util.find_library() where util is imported from ctypes
                if isinstance(val, ast.Name) and val.id in mod_names or (isinstance(val, ast.Attribute)
                      and val.attr == "util"
                      and isinstance(val.value, ast.Name)
                      and val.value.id in mod_names):
                    is_ctypes = True
                if is_ctypes:
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
