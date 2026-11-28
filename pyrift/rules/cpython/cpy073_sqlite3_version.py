"""
CPY073 — sqlite3.version / version_info deprecated 3.12, removed 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
sqlite3.version and sqlite3.version_info were deprecated in Python 3.12
(gh-93370) and removed in Python 3.14 (gh-118924).

These attributes exposed the pysqlite binding version (e.g. "2.6.0"),
not the SQLite C library version, which made them confusing and useless.
They raise DeprecationWarning on 3.12–3.13 and AttributeError on 3.14+.

Replacement: sqlite3.sqlite_version (string) / sqlite3.sqlite_version_info
            (tuple) — these expose the actual SQLite C library version and
            have been available since Python 3.0.

Detects:
  sqlite3.version          # attribute-access form
  sqlite3.version_info
  from sqlite3 import version
  from sqlite3 import version_info
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED_ATTRS = frozenset({"version", "version_info"})


class Sqlite3VersionRemovedRule(BaseRule):
    rule_id = "CPY073"
    title   = "sqlite3.version/version_info deprecated 3.12, removed 3.14"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # from sqlite3 import version / version_info
            if isinstance(n, ast.ImportFrom) and n.module == "sqlite3":
                for alias in n.names:
                    if alias.name in _REMOVED_ATTRS:
                        findings.append(self._make(filename, alias.name, alias.lineno, alias.col_offset))

            # sqlite3.version / sqlite3.version_info (attribute access)
            if (isinstance(n, ast.Attribute)
                    and n.attr in _REMOVED_ATTRS
                    and isinstance(n.value, ast.Name)
                    and n.value.id == "sqlite3"):
                findings.append(self._make(filename, n.attr, n.lineno, n.col_offset))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, attr_name: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename, line=line, col=col,
            rule_id=self.rule_id, title=self.title,
            description=(
                f"sqlite3.{attr_name} was deprecated in Python 3.12 and "
                "removed in Python 3.14. It exposed the pysqlite binding "
                "version (not the SQLite C library version), which made it "
                "misleading and unnecessary."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.12",
            docs_url="https://docs.python.org/3/whatsnew/3.14.html#removed",
            suggestion=(
                f"Replace sqlite3.{attr_name} with sqlite3.sqlite_version "
                f"(string) or sqlite3.sqlite_version_info (tuple), which "
                f"expose the actual SQLite C library version."
            ),
        )
