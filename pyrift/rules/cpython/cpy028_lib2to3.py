"""CPY028 -- lib2to3 removed in Python 3.13."""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class Lib2to3Rule(BaseRule):
    rule_id = "CPY028"
    title = "lib2to3 removed in Python 3.13"
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
            mod = info.module or ""
            if mod == "lib2to3" or mod.startswith("lib2to3."):
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        "lib2to3 was deprecated in Python 3.11 and removed "
                        "in Python 3.13. Importing it raises ModuleNotFoundError "
                        "on Python 3.13+."
                    ),
                    severity=Severity.ERROR, runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "Use libcst or ast for modern Python AST manipulation: "
                        "pip install libcst"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.13.html"
                        "#removed-modules-and-packages"
                    ),
                ))
        return findings