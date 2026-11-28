"""
CPY075 — http.server.CGIHTTPRequestHandler deprecated in 3.13, removed in 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
http.server.CGIHTTPRequestHandler was deprecated in Python 3.13 and
removed in Python 3.15. The --cgi flag to ``python -m http.server`` was
deprecated and removed at the same time. No direct replacement exists;
the official documentation states: "Anything is better than CGI to
interface a web server with a request handler."

Detects:
  from http.server import CGIHTTPRequestHandler
  import http.server; http.server.CGIHTTPRequestHandler
  CGIHTTPRequestHandler  (bare Name – implies prior import)

References:
  gh-109096  https://github.com/python/cpython/issues/109096
  What's New 3.13 (deprecated): https://docs.python.org/3/whatsnew/3.13.html#deprecated
  What's New 3.15 (removed):   https://docs.python.org/3/whatsnew/3.15.html#removed
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_HANDLER = "CGIHTTPRequestHandler"


class HttpServerCGIHandlerRule(BaseRule):
    rule_id = "CPY075"
    title   = "http.server.CGIHTTPRequestHandler deprecated 3.13, removed in 3.15"
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
            # from http.server import CGIHTTPRequestHandler
            if isinstance(n, ast.ImportFrom) and n.module == "http.server":
                for alias in n.names:
                    if alias.name == _HANDLER:
                        findings.append(
                            self._make(filename, alias.lineno, alias.col_offset)
                        )

            # bare CGIHTTPRequestHandler (Name node) – implies prior import
            elif isinstance(n, ast.Name) and n.id == _HANDLER or (
                isinstance(n, ast.Attribute)
                and n.attr == _HANDLER
                and isinstance(n.value, ast.Attribute)
                and n.value.attr == "server"
                and isinstance(n.value.value, ast.Name)
                and n.value.value.id == "http"
            ):
                findings.append(self._make(filename, n.lineno, n.col_offset))

        # Deduplicate by (line, col) – alias-level positions are unique so
        # multi-import statements produce one finding per alias.
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
                "Python 3.13 and removed in Python 3.15. "
                "The --cgi flag to 'python -m http.server' was removed at "
                "the same time. The class was obsolete, rarely used, and "
                "carries significant security risk."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.13",
            affected_until="",
            suggestion=(
                "No direct replacement exists. The official documentation "
                "recommends replacing CGI-based handlers with a proper WSGI "
                "or ASGI framework (e.g. Flask, FastAPI, Gunicorn, uWSGI). "
                "For simple static file serving, use "
                "http.server.SimpleHTTPRequestHandler or "
                "'python -m http.server' without the --cgi flag."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.15.html#removed",
        )