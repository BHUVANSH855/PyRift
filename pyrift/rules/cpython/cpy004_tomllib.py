"""
CPY004 -- tomllib requires Python 3.11+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
tomllib was added to the standard library in Python 3.11 (PEP 680).
On Python 3.10 and below, importing tomllib raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class TomllibRule(BaseRule):
    rule_id = "CPY004"
    title = "tomllib requires Python 3.11+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        imp_map = collect_imports(node)
        findings: list[Finding] = []

        for info in imp_map.get("tomllib", min_version=(3, 11)):
            findings.append(Finding(
                file=filename,
                line=info.line,
                col=info.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "tomllib was added to the standard library in "
                    "Python 3.11 (PEP 680). On Python 3.10 and below, "
                    "importing tomllib raises ModuleNotFoundError."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.0",
                affected_until="3.10",
                suggestion=(
                    "Guard with a try/except: "
                    "try: import tomllib "
                    "except ModuleNotFoundError: import tomli as tomllib  "
                    "(pip install tomli)"
                ),
                docs_url="https://peps.python.org/pep-0680/",
            ))

        return findings