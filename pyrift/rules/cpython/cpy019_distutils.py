"""CPY019 -- distutils removed from the Python standard library in 3.12+."""

from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

DISTUTILS_MODULES = {
    "distutils",
    "distutils.core",
    "distutils.cmd",
    "distutils.command",
    "distutils.config",
    "distutils.dist",
    "distutils.extension",
    "distutils.fancy_getopt",
    "distutils.file_util",
    "distutils.log",
    "distutils.spawn",
    "distutils.sysconfig",
    "distutils.text_file",
    "distutils.unixccompiler",
    "distutils.util",
    "distutils.version",
}


class DistutilsRule(BaseRule):
    rule_id = "CPY019"
    title = "distutils removed from the Python standard library in 3.12+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        imp_map = collect_imports(node)

        for info in imp_map.by_statement():
            mod = info.module or ""

            if mod in DISTUTILS_MODULES or mod.startswith("distutils."):
                findings.append(
                    Finding(
                        file=filename,
                        line=info.line,
                        col=info.col,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"'{mod}' uses distutils, which was deprecated "
                            "in Python 3.10 and removed from the Python "
                            "standard library in Python 3.12 (PEP 632)."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.12",
                        suggestion=(
                            "Migrate from distutils to its supported "
                            "replacement. PEP 632 recommends setuptools "
                            "for several APIs, packaging for "
                            "distutils.version, shutil.which for "
                            "distutils.spawn.find_executable, and "
                            "sysconfig for distutils.sysconfig."
                        ),
                        docs_url="https://peps.python.org/pep-0632/",
                    )
                )

        return findings
