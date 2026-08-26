"""PPY035 -- C extension packages may not work correctly on PyPy."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Confidence, Finding, Runtime, Severity

KNOWN_PROBLEMATIC = {
    "numpy", "pandas", "scipy", "torch", "tensorflow",
    "psycopg2", "lxml", "Pillow", "PIL", "cv2",
    "sklearn", "matplotlib", "cryptography",
}


class CExtensionsRule(BaseRule):
    rule_id = "PPY035"
    title = "C extension packages may not work correctly on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        imp_map = collect_imports(node)
        seen: set[str] = set()

        for info in imp_map.imports:
            base = (info.module or "").split(".")[0]
            if base in KNOWN_PROBLEMATIC and base not in seen:
                seen.add(base)
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        f"'{base}' is a C extension package. PyPy's C API "
                        "compatibility layer (cpyext) is not 100% complete — "
                        "some packages work, some crash, some produce wrong results."
                    ),
                    severity=Severity.WARNING,
                    confidence=Confidence.HIGH,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        f"Check PyPy compatibility for '{base}' at "
                        "https://pypy.org/compat.html before deploying on PyPy. "
                        "Consider cffi-based alternatives where available."
                    ),
                    docs_url="https://doc.pypy.org/en/latest/cpython_differences.html",
                ))
        return findings