"""
CPY076 — ssl.wrap_socket() removed in Python 3.12
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ssl.wrap_socket() was deprecated in Python 3.7 and removed in Python 3.12.
It was a convenience function that created an SSL-wrapped socket. Use
SSLContext.wrap_socket() instead.

Detects:
  ssl.wrap_socket(...)
  from ssl import wrap_socket
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class SslWrapSocketRule(BaseRule):
    rule_id = "CPY076"
    title   = "ssl.wrap_socket() removed in Python 3.12"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # from ssl import wrap_socket
            if isinstance(n, ast.ImportFrom) and n.module == "ssl":
                for alias in n.names:
                    if alias.name == "wrap_socket":
                        findings.append(self._make(filename, n.lineno, n.col_offset))

            # ssl.wrap_socket(...)
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Attribute)
                        and func.attr == "wrap_socket"
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "ssl"):
                    findings.append(self._make(filename, n.lineno, n.col_offset))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename, line=line, col=col,
            rule_id=self.rule_id, title=self.title,
            description=(
                "ssl.wrap_socket() was deprecated in Python 3.7 and removed "
                "in Python 3.12. It was a convenience function that bypassed "
                "proper SSL context configuration."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.12",
            suggestion=(
                "Create an SSLContext and use context.wrap_socket() instead: "
                "ctx = ssl.create_default_context(); "
                "ctx.wrap_socket(sock, server_hostname=hostname)"
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.12.html",
        )
