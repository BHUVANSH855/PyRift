"""CPY049 -- compression.zstd requires Python 3.14+."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class CompressionZstdRule(BaseRule):
    rule_id = "CPY049"
    title = "compression.zstd requires Python 3.14+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            if info.module and info.module.startswith("compression"):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        "The compression.zstd module was added in Python 3.14. "
                        "Importing it on Python 3.13 or below raises ModuleNotFoundError."
                    ),
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.0", affected_until="3.13",
                    suggestion=(
                        "Guard with: if sys.version_info >= (3, 14): import compression.zstd "
                        "For 3.13 compatibility use: pip install zstandard"
                    ),
                    docs_url="https://docs.python.org/3/whatsnew/3.14.html",
                ))
        return findings