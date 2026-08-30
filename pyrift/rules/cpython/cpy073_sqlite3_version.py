"""
CPY073 — sqlite3.version / version_info removed in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
sqlite3.version and sqlite3.version_info were deprecated in Python 3.12
and removed in Python 3.14. These exposed the SQLite C library version,
which was misleading since it did not reflect the Python binding version.

Detects:
  sqlite3.version
  sqlite3.version_info
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED_ATTRS = {"version", "version_info"}


class Sqlite3VersionRemovedRule(BaseRule):
    rule_id = "CPY073"
    title   = "sqlite3.version/version_info removed in Python 3.14"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if (isinstance(n, ast.Attribute)
                    and n.attr in _REMOVED_ATTRS
                    and isinstance(n.value, ast.Name)
                    and n.value.id == "sqlite3"):
                findings.append(Finding(
                    file=filename, line=n.lineno, col=n.col_offset,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        f"sqlite3.{n.attr} was deprecated in Python 3.12 and "
                        "removed in Python 3.14. It exposed the SQLite C library "
                        "version, which was misleading and unnecessary."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.14",
                    suggestion=(
                        "Use sqlite3.sqlite_version to get the SQLite C library "
                        "version, or check the Python sqlite3 module version via "
                        "importlib.metadata.version('sqlite3')."
                    ),
                    docs_url="https://docs.python.org/3/whatsnew/3.14.html",
                ))
        return findings
