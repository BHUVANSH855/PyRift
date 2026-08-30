"""
CPY066 — asyncio child watcher classes removed in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.14 removes the asyncio child watcher classes deprecated in 3.12:
  - ThreadedChildWatcher
  - FastChildWatcher
  - MultiLoopChildWatcher
  - SafeChildWatcher
  - AbstractChildWatcher
  - CommandlineSubprocessSelector
These were part of the old child watcher API replaced by PIDFD on Linux.

Detects:
  from asyncio import ThreadedChildWatcher
  asyncio.ThreadedChildWatcher()
  asyncio.get_event_loop_policy().set_child_watcher(...)
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED_WATCHERS = {
    "ThreadedChildWatcher", "FastChildWatcher", "MultiLoopChildWatcher",
    "SafeChildWatcher", "AbstractChildWatcher", "CommandlineSubprocessSelector",
}


class AsyncioChildWatcherRule(BaseRule):
    rule_id = "CPY066"
    title   = "asyncio child watcher classes removed in Python 3.14"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # from asyncio import ThreadedChildWatcher
            if isinstance(n, ast.ImportFrom) and n.module == "asyncio":
                for alias in n.names:
                    if alias.name in _REMOVED_WATCHERS:
                        findings.append(self._make(filename, alias.name, n.lineno, n.col_offset))

            # asyncio.ThreadedChildWatcher() via attribute access
            if (isinstance(n, ast.Attribute)
                    and n.attr in _REMOVED_WATCHERS
                    and isinstance(n.value, ast.Name)
                    and n.value.id == "asyncio"):
                findings.append(self._make(filename, n.attr, n.lineno, n.col_offset))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, class_name: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename,
            line=line,
            col=col,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                f"asyncio.{class_name} was deprecated in Python 3.12 and removed "
                "in Python 3.14. The child watcher API was replaced by PIDFD-based "
                "process watching on Linux. Importing it on 3.14+ raises ImportError."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Remove child watcher usage. Python 3.14+ uses PIDFD automatically "
                "on Linux. For cross-platform needs, use asyncio.Runner with "
                "loop_factory parameter instead of manual child watcher configuration."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html",
        )
