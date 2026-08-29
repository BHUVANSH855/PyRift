"""
CPY052 — threading.local() semantics differ in free-threaded Python 3.13+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In standard CPython, threading.local() provides thread-local storage
that is protected by the GIL. In free-threaded Python 3.13+ builds,
threading.local() still works but the semantics of accessing it
concurrently change — reads and writes are no longer atomic and
code that assumed GIL-protected atomicity may silently break.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class FreeThreadedThreadingLocalRule(BaseRule):
    rule_id = "CPY052"
    title   = "threading.local() atomicity assumptions break in free-threaded 3.13+"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "local" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "threading"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "threading.local() is used here. In standard CPython, "
                        "the GIL makes threading.local() access implicitly "
                        "atomic. In Python 3.13+ free-threaded builds (PEP 703, "
                        "no-GIL mode), this atomicity guarantee is removed. "
                        "Code that reads and writes threading.local() attributes "
                        "without explicit synchronisation may silently produce "
                        "incorrect results under concurrent access."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "If running in free-threaded mode, add explicit "
                        "synchronisation around threading.local() access. "
                        "Check sys.flags.nogil to detect free-threaded mode: "
                        "if getattr(sys.flags, 'nogil', False): use locks."
                    ),
                    docs_url="https://peps.python.org/pep-0703/",
                ))
        return findings