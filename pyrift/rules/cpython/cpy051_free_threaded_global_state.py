"""
CPY051 — Global state mutation unsafe in free-threaded Python 3.13+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.13+ introduced an experimental free-threaded build mode
that disables the GIL (PEP 703). Code that mutates module-level
or class-level mutable state (lists, dicts, sets) without locks
relies on the GIL for thread safety. In free-threaded builds,
this silently causes race conditions and data corruption.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class FreeThreadedGlobalStateRule(BaseRule):
    rule_id = "CPY051"
    title   = "Global mutable state mutation unsafe in free-threaded Python 3.13+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        # Find module-level mutable assignments (lists, dicts, sets)
        for n in ast.walk(node):
            if not isinstance(n, ast.Module):
                continue
            for stmt in n.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                # Check if value is a mutable literal
                if isinstance(stmt.value, (ast.List, ast.Dict, ast.Set)):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            findings.append(Finding(
                                file=filename,
                                line=stmt.lineno,
                                col=stmt.col_offset,
                                rule_id=self.rule_id,
                                title=self.title,
                                description=(
                                    f"Module-level mutable variable "
                                    f"'{target.id}' is defined here. "
                                    "In Python 3.13+ free-threaded builds "
                                    "(PEP 703, no-GIL mode), the GIL no longer "
                                    "protects shared mutable state. Concurrent "
                                    "mutation of module-level lists, dicts, or "
                                    "sets from multiple threads silently causes "
                                    "race conditions and data corruption."
                                ),
                                severity=Severity.WARNING,
                                runtime=Runtime.CPYTHON,
                                affected_from="3.13",
                                suggestion=(
                                    "Protect shared mutable state with locks: "
                                    "import threading; _lock = threading.Lock() "
                                    "and use 'with _lock:' around mutations. "
                                    "Or use thread-safe alternatives like "
                                    "queue.Queue for inter-thread communication."
                                ),
                                docs_url="https://peps.python.org/pep-0703/",
                            ))
        return findings