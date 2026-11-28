"""
CPY097 -- wave.Wave_read / Wave_write mark methods removed (3.15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``wave`` module's ``Wave_read`` and ``Wave_write`` classes contained
three methods for AIFF-style mark handling that were always no-ops on WAVE
files:

    Wave_read.getmark(id)
    Wave_read.getmarkers()
    Wave_write.setmark(id, pos, name)
    Wave_write.getmarkers()

These methods were deprecated in Python 3.13 and removed in 3.15.

Reference: https://docs.python.org/3/whatsnew/3.15.html#removed
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED_METHODS = frozenset({"getmark", "setmark", "getmarkers"})


class WaveMarkMethodsRemovedRule(BaseRule):
    rule_id = "CPY097"
    title = "wave mark methods (getmark/setmark/getmarkers) removed in Python 3.15"
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
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr in _REMOVED_METHODS
            ):
                continue
            has_wave_import = any(
                (isinstance(stmt, ast.Import)
                 and any(alias.name == "wave" for alias in stmt.names))
                or (isinstance(stmt, ast.ImportFrom)
                    and stmt.module == "wave")
                for stmt in ast.walk(node)
                if isinstance(stmt, (ast.Import, ast.ImportFrom))
            )
            if not has_wave_import:
                continue
            method = func.attr
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f".{method}() is a wave mark method that was deprecated "
                    "in Python 3.13 and removed in 3.15. WAVE files do not "
                    "support marks; these methods were always no-ops. "
                    "Calling them raises AttributeError in Python 3.15+."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.15",
                suggestion=(
                    f"Remove the .{method}() call. WAVE files have no "
                    "mark support; if you need AIFF mark handling, use "
                    "the aifc module (itself deprecated) or a third-party "
                    "audio library."
                ),
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.15.html#removed"
                ),
                whatsnew_ref="3.15#removed",
            ))
        return findings
