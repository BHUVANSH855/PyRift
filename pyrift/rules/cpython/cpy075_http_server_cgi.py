"""
CPY075 — http.server.CGIHTTPRequestHandler deprecated in 3.13, removed in 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
http.server.CGIHTTPRequestHandler was deprecated in Python 3.13 and
will be removed in Python 3.15. It provided CGI script execution support
which is a security risk and rarely needed.

Detects:
  from http.server import CGIHTTPRequestHandler
  http.server.CGIHTTPRequestHandler
  CGIHTTPRequestHandler
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class HttpServerCGIHandlerRule(BaseRule):
    rule_id = "CPY075"
    title   = "http.server.CGIHTTPRequestHandler deprecated in 3.13, removed in 3.15"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # from http.server import CGIHTTPRequestHandler
            if isinstance(n, ast.ImportFrom) and n.module == "http.server":
                for alias in n.names:
                    if alias.name == "CGIHTTPRequestHandler":
                        findings.append(self._make(filename, n.lineno, n.col_offset))

            # http.server.CGIHTTPRequestHandler or just CGIHTTPRequestHandler
            if isinstance(n, ast.Name) and n.id == "CGIHTTPRequestHandler":
                findings.append(self._make(filename, n.lineno, n.col_offset))

            # http.server.CGIHTTPRequestHandler via attribute access
            if (isinstance(n, ast.Attribute)
                    and n.attr == "CGIHTTPRequestHandler"
                    and isinstance(n.value, ast.Attribute)
                    and n.value.attr == "server"
                    and isinstance(n.value.value, ast.Name)
                    and n.value.value.id == "http"):
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
                "http.server.CGIHTTPRequestHandler was deprecated in "
                "Python 3.13 and will be removed in Python 3.15. It provided "
                "CGI script execution support which is a security risk."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.CPYTHON,
            affected_from="3.13",
            affected_until="3.15",
            suggestion=(
                "Use http.server.SimpleHTTPRequestHandler instead, or use "
                "a dedicated web server for CGI functionality."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.13.html",
        )