"""
pyrift.scanner
~~~~~~~~~~~~~~
Core scanning engine.
Parses Python files into ASTs and runs all registered rules.
"""
from __future__ import annotations
import ast
import os
from pathlib import Path
from typing import Iterator

from .finding import Finding
from .base_rule import BaseRule

from .rules.cpython.cpy001_dict_ordering     import DictOrderingRule
from .rules.cpython.cpy002_exception_notes   import ExceptionNotesRule
from .rules.cpython.cpy003_union_type_syntax import UnionTypeSyntaxRule
from .rules.cpython.cpy004_tomllib           import TomllibRule
from .rules.cpython.cpy005_match_case        import MatchCaseRule
from .rules.cpython.cpy006_asyncio_timeout   import AsyncioTimeoutRule
from .rules.cpython.cpy007_removed_modules   import RemovedModulesRule
from .rules.pypy.ppy001_gc_finalizer         import GcFinalizerRule
from .rules.pypy.ppy002_ctypes               import CtypesRule
from .rules.pypy.ppy003_getrefcount          import GetRefcountRule
from .rules.pypy.ppy004_weakref_proxy        import WeakrefProxyRule

ALL_RULES: list[BaseRule] = [
    DictOrderingRule(),
    ExceptionNotesRule(),
    UnionTypeSyntaxRule(),
    TomllibRule(),
    MatchCaseRule(),
    AsyncioTimeoutRule(),
    RemovedModulesRule(),
    GcFinalizerRule(),
    CtypesRule(),
    GetRefcountRule(),
    WeakrefProxyRule(),
]

SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env",
    "node_modules", ".tox", "dist", "build", ".eggs",
}


class ScanResult:
    """Holds all findings from a scan run."""

    def __init__(self, findings: list[Finding], files_scanned: int):
        self.findings      = findings
        self.files_scanned = files_scanned

    @property
    def errors(self) -> list[Finding]:
        from .finding import Severity
        return [f for f in self.findings if f.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        from .finding import Severity
        return [f for f in self.findings if f.severity == Severity.WARNING]

    @property
    def score(self) -> int:
        deductions = len(self.errors) * 10 + len(self.warnings) * 3
        return max(0, 100 - deductions)

    def __repr__(self) -> str:
        return (
            f"ScanResult(files={self.files_scanned}, "
            f"errors={len(self.errors)}, warnings={len(self.warnings)}, "
            f"score={self.score})"
        )


def _python_files(path: Path) -> Iterator[Path]:
    if path.is_file():
        if path.suffix == ".py":
            yield path
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield Path(root) / f


def scan_file(filepath: str | Path,
              rules: list[BaseRule] | None = None) -> list[Finding]:
    """Scan a single file. Returns list of Findings."""
    filepath = Path(filepath)
    rules = rules or ALL_RULES
    findings: list[Finding] = []

    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree   = ast.parse(source, filename=str(filepath))
    except SyntaxError as exc:
        from .finding import Severity, Runtime
        findings.append(Finding(
            file=str(filepath),
            line=exc.lineno or 0,
            rule_id="PARSE",
            title="Syntax error — file could not be parsed",
            description=str(exc),
            severity=Severity.ERROR,
            runtime=Runtime.BOTH,
        ))
        return findings

    for rule in rules:
        try:
            findings.extend(rule.check(tree, str(filepath)))
        except Exception:
            pass

    return findings


def scan(path: str | Path,
         rules: list[BaseRule] | None = None) -> ScanResult:
    """
    Scan a file or directory tree.

    Usage::

        import pyrift
        result = pyrift.scan("./myproject")
        for f in result.findings:
            print(f)
    """
    path = Path(path)
    all_findings: list[Finding] = []
    files_scanned = 0

    for py_file in _python_files(path):
        all_findings.extend(scan_file(py_file, rules))
        files_scanned += 1

    return ScanResult(all_findings, files_scanned)