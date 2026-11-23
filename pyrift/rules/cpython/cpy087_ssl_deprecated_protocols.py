"""
CPY087 -- ssl deprecated protocol constants and options (pending removal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Several ``ssl`` module constants are deprecated and pending removal:

- ``ssl.PROTOCOL_TLS`` -- use ``ssl.PROTOCOL_TLS_CLIENT`` or
  ``ssl.PROTOCOL_TLS_SERVER``
- ``ssl.PROTOCOL_TLSv1`` -- TLS 1.0, insecure
- ``ssl.PROTOCOL_TLSv1_1`` -- TLS 1.1, insecure
- ``ssl.PROTOCOL_TLSv1_2`` -- use ``ssl.PROTOCOL_TLS_CLIENT``
- ``ssl.PROTOCOL_SSLv23`` -- alias for PROTOCOL_TLS, deprecated
- ``ssl.OP_NO_SSLv2`` -- SSLv2 already removed
- ``ssl.OP_NO_SSLv3`` -- SSLv3 already removed
- ``ssl.OP_NO_TLSv1`` -- use minimum_version instead
- ``ssl.OP_NO_TLSv1_1`` -- use minimum_version instead
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_DEPRECATED_PROTOCOLS = frozenset({
    "PROTOCOL_TLS",
    "PROTOCOL_TLSv1",
    "PROTOCOL_TLSv1_1",
    "PROTOCOL_TLSv1_2",
    "PROTOCOL_SSLv23",
    "OP_NO_SSLv2",
    "OP_NO_SSLv3",
    "OP_NO_TLSv1",
    "OP_NO_TLSv1_1",
})


class SslDeprecatedProtocolsRule(BaseRule):
    rule_id = "CPY087"
    title = "ssl deprecated protocol constants pending removal"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Attribute):
                continue
            if n.attr not in _DEPRECATED_PROTOCOLS:
                continue
            if not (isinstance(n.value, ast.Name) and n.value.id == "ssl"):
                continue
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"ssl.{n.attr} is deprecated and pending removal. "
                    "Using deprecated SSL/TLS protocol constants may "
                    "enable insecure connections or fail on future "
                    "Python versions."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.10",
                suggestion=(
                    "Use ssl.PROTOCOL_TLS_CLIENT or "
                    "ssl.PROTOCOL_TLS_SERVER with "
                    "SSLContext.minimum_version set to "
                    "ssl.TLSVersion.TLSv1_2 or higher. "
                    "Avoid specifying TLS versions via OP_NO_* flags."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/ssl.html"
                    "#security-considerations"
                ),
            ))
        return findings