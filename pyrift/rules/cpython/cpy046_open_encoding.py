"""
CPY046 — open() without encoding= silently uses platform encoding before 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before Python 3.15, open() in text mode uses the platform's locale encoding
by default — UTF-8 on Linux/Mac but often CP1252 or Latin-1 on Windows.
Python 3.15 makes UTF-8 the default on all platforms (PEP 686).
Code that opens files without explicit encoding= may silently read/write
wrong characters on Windows with Python < 3.15.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

WRITE_READ_MODES = {"r", "w", "a", "r+", "w+", "a+", "x"}


class OpenEncodingRule(BaseRule):
    rule_id = "CPY046"
    title   = "open() without encoding= uses platform-dependent encoding before 3.15"
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
            is_open = (
                isinstance(func, ast.Name) and func.id == "open"
            )
            if not is_open:
                continue
            # Check mode — only flag text mode (not binary)
            mode = "r"
            for i, arg in enumerate(n.args):
                if i == 1 and isinstance(arg, ast.Constant):
                    mode = str(arg.value)
            for kw in n.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)

            # Binary mode — skip
            if "b" in mode:
                continue

            # Check if encoding= is already specified
            has_encoding = any(kw.arg == "encoding" for kw in n.keywords)
            if has_encoding:
                continue

            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "open() is called in text mode without an explicit "
                    "encoding= argument. Before Python 3.15, the default "
                    "encoding is the platform locale — UTF-8 on Linux/Mac "
                    "but often CP1252 or Latin-1 on Windows. This silently "
                    "causes encoding errors or data corruption when code runs "
                    "on different platforms. Python 3.15 (PEP 686) makes "
                    "UTF-8 the universal default."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.0",
                affected_until="3.14",
                suggestion=(
                    "Always specify encoding explicitly: "
                    "open(file, encoding='utf-8') "
                    "This works correctly on all Python versions and platforms."
                ),
                docs_url="https://peps.python.org/pep-0686/",
            ))
        return findings