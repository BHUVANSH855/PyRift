"""
CPY007 -- Modules removed in Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PEP 594 removed many legacy stdlib modules in 3.13.
Importing them on 3.13+ raises ModuleNotFoundError.

Detects both static and dynamic imports:
  import cgi                           (static)
  importlib.import_module('cgi')       (dynamic)
  __import__('cgi')                    (dynamic)
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_dynamic_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

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
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        # Static imports
        for n in ast.walk(node):
            mod = None
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name in REMOVED_313:
                        mod = alias.name
                        line, col = n.lineno, n.col_offset
            elif isinstance(n, ast.ImportFrom) and n.module in REMOVED_313:
                mod = n.module
                line, col = n.lineno, n.col_offset

            if mod:
                findings.append(self._make(filename, mod, line, col))

        # Dynamic imports: importlib.import_module('cgi') / __import__('cgi')
        for info in collect_dynamic_imports(node):
            base = info.module.split(".")[0]
            if base in REMOVED_313:
                findings.append(self._make(
                    filename, info.module, info.line, info.col,
                    dynamic=True
                ))

        return findings

    def _make(self, filename: str, mod: str, line: int, col: int,
              dynamic: bool = False) -> Finding:
        how = "dynamically imported" if dynamic else "imported"
        return Finding(
            file=filename,
            line=line,
            col=col,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                f"The '{mod}' module was {how} but was removed from the "
                "Python standard library in Python 3.13 (PEP 594). "
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
        )