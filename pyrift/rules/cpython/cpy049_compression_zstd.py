"""
CPY049 — compression.zstd requires Python 3.14+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The compression.zstd module was added in Python 3.14 providing
native Zstandard compression support. Importing it on Python 3.13
or below raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class CompressionZstdRule(BaseRule):
    rule_id = "CPY049"
    title   = "compression.zstd requires Python 3.14+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name in ("compression.zstd", "compression"):
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("compression"):
                    mod = n.module
                    line, col = n.lineno, n.col_offset
            if mod:
                findings.append(Finding(
                    file=filename,
                    line=line,
                    col=col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The compression.zstd module was added in Python 3.14. "
                        "It provides native Zstandard compression support. "
                        "Importing it on Python 3.13 or below raises "
                        "ModuleNotFoundError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.13",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 14): "
                        "import compression.zstd "
                        "For 3.13 compatibility use the zstandard package: "
                        "pip install zstandard"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.14.html"
                    ),
                ))
        return findings