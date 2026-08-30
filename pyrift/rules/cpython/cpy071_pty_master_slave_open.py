"""
CPY071 — pty.master_open()/slave_open() removed in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pty.master_open() and pty.slave_open() were deprecated in Python 3.12
and removed in Python 3.14. Use pty.openpty() instead, which returns
a (master_fd, slave_fd) tuple.

Detects:
  pty.master_open()
  pty.slave_open()
  from pty import master_open
  from pty import slave_open
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED = {"master_open", "slave_open"}


class PtyMasterSlaveOpenRule(BaseRule):
    rule_id = "CPY071"
    title   = "pty.master_open()/slave_open() removed in Python 3.14"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # from pty import master_open / slave_open
            if isinstance(n, ast.ImportFrom) and n.module == "pty":
                for alias in n.names:
                    if alias.name in _REMOVED:
                        findings.append(self._make(filename, alias.name, n.lineno, n.col_offset))

            # pty.master_open() / pty.slave_open()
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Attribute)
                        and func.attr in _REMOVED
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "pty"):
                    findings.append(self._make(filename, func.attr, n.lineno, n.col_offset))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, func_name: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename, line=line, col=col,
            rule_id=self.rule_id, title=self.title,
            description=(
                f"pty.{func_name}() was deprecated in Python 3.12 and removed "
                "in Python 3.14. It was a legacy function from the original "
                "pty module implementation."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Use pty.openpty() which returns a (master_fd, slave_fd) tuple. "
                "For slave file naming, use os.ttyname(slave_fd)."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html",
        )
