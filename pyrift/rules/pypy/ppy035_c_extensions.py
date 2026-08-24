"""
PPY035 — CPython C extension modules may not load on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CPython C extensions (.pyd / .so files built against CPython's
C API) may not load on PyPy. PyPy has its own C API compatibility
layer (cpyext) but it is not 100% complete. Some extensions work,
some crash, and some silently produce wrong results on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

# Known C-extension-heavy packages that commonly fail or have issues on PyPy
KNOWN_PROBLEMATIC = {
    "numpy", "scipy", "pandas", "lxml",
    "Pillow", "PIL", "cv2", "torch",
    "tensorflow", "sklearn", "psycopg2",
    "cryptography", "cffi", "cython",
}


class CExtensionsRule(BaseRule):
    rule_id = "PPY035"
    title   = "C extension packages may not work correctly on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    base = alias.name.split(".")[0]
                    if base in KNOWN_PROBLEMATIC:
                        mod = base
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    base = n.module.split(".")[0]
                    if base in KNOWN_PROBLEMATIC:
                        mod = base
                        line, col = n.lineno, n.col_offset
            if mod:
                findings.append(Finding(
                    file=filename,
                    line=line,
                    col=col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"'{mod}' is a C extension package. CPython C "
                        "extensions may not load on PyPy, or may load "
                        "but produce incorrect results. PyPy's C API "
                        "compatibility layer (cpyext) is not 100% complete."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        f"Check PyPy compatibility for '{mod}' at "
                        "https://pypy.org/compat.html before running "
                        "on PyPy. Consider using cffi-based alternatives "
                        "which are fully supported on PyPy."
                    ),
                    docs_url="https://pypy.org/compat.html",
                ))
        return findings