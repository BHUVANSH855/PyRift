"""
CPY076 — ssl.wrap_socket() deprecated 3.7, removed 3.12
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ssl.wrap_socket() was deprecated in Python 3.7 and hard-removed in
Python 3.12. The function sends no SNI TLS extension and performs no
hostname validation, making it both API-broken and insecure.

Detects:
  from ssl import wrap_socket
  ssl.wrap_socket(...)       (attribute-access call)

Does NOT detect bare ``wrap_socket(...)`` Name calls to avoid false
positives from local aliases; the import and attribute-access forms are
the unambiguous signal.

References:
  gh-94199  https://github.com/python/cpython/issues/94199
  What's New 3.12 (removed): https://docs.python.org/3/whatsnew/3.12.html#ssl
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class SslWrapSocketRule(BaseRule):
    rule_id = "CPY076"
    title   = "ssl.wrap_socket() deprecated 3.7, removed 3.12"
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
            # from ssl import wrap_socket
            if isinstance(n, ast.ImportFrom) and n.module == "ssl":
                for alias in n.names:
                    if alias.name == "wrap_socket":
                        findings.append(
                            self._make(filename, alias.lineno, alias.col_offset)
                        )

            # ssl.wrap_socket(...)  — attribute-access call form
            elif isinstance(n, ast.Call):
                func = n.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "wrap_socket"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "ssl"
                ):
                    findings.append(self._make(filename, n.lineno, n.col_offset))

        # Deduplicate by (line, col) — alias-level positions are unique so
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
                "ssl.wrap_socket() was deprecated in Python 3.7 and removed "
                "in Python 3.12. The function sends no SNI TLS extension and "
                "performs no hostname validation, making it insecure. "
                "Any code still using it is broken on Python 3.12+."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.7",
            suggestion=(
                "Create an ssl.SSLContext and call its wrap_socket() method: "
                "ctx = ssl.create_default_context(); "
                "wrapped = ctx.wrap_socket(sock, server_hostname=hostname). "
                "For server-side sockets: ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); "
                "ctx.load_cert_chain(certfile, keyfile); "
                "wrapped = ctx.wrap_socket(sock, server_side=True)."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.12.html#ssl",
        )