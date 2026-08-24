"""
CPY007 — Modules removed in Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PEP 594 removed many legacy stdlib modules in 3.13.
Importing them on 3.13+ raises ModuleNotFoundError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

# Modules removed in Python 3.13 per PEP 594
REMOVED_313 = {
    "aifc", "audioop", "cgi", "cgitb", "chunk", "crypt",
    "imghdr", "mailcap", "msilib", "nis", "nntplib",
    "ossaudiodev", "pipes", "sndhdr", "spwd", "sunau",
    "telnetlib", "uu", "xdrlib",
    # also removed
    "asynchat", "asyncore", "smtpd",
}


class RemovedModulesRule(BaseRule):
    rule_id = "CPY007"
    title   = "Module removed in Python 3.13"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name in REMOVED_313:
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom):
                if n.module in REMOVED_313:
                    mod = n.module
                    line, col = n.lineno, n.col_offset

            if mod:
                findings.append(Finding(
                    file=filename,
                    line=line,
                    col=col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"The '{mod}' module was removed from the Python "
                        "standard library in Python 3.13 (PEP 594). "
                        "Importing it on 3.13+ raises ModuleNotFoundError."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        f"Find a third-party replacement for '{mod}' on PyPI, "
                        "or vendor the module directly if needed."
                    ),
                    docs_url="https://peps.python.org/pep-0594/",
                ))

        return findings