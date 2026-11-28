"""
CPY070 — asyncio event loop policy deprecated in 3.14, removed in 3.16
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.14 deprecates the entire asyncio event loop policy system
(gh-127949, contributed by Kumar Aditya).  All six names below carry
``.. deprecated:: 3.14`` in the CPython docs and are scheduled for
removal in Python 3.16:

  - asyncio.get_event_loop_policy()
  - asyncio.set_event_loop_policy()
  - asyncio.AbstractEventLoopPolicy
  - asyncio.DefaultEventLoopPolicy
  - asyncio.WindowsSelectorEventLoopPolicy  (Windows only)
  - asyncio.WindowsProactorEventLoopPolicy  (Windows only)

Use asyncio.run() or asyncio.Runner(loop_factory=...) instead.

Detects:
  asyncio.<name>(...)          — calls on policy functions
  asyncio.<name>               — attribute access on policy classes
  from asyncio import <name>   — import of any of the six names

Evidence:
  - Deprecated 3.14: https://github.com/python/cpython/issues/127949
  - Removal  3.16:   https://docs.python.org/3/deprecations/pending-removal-in-3.16.html
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

# Functions deprecated in 3.14 (called with parentheses)
_POLICY_FUNCTIONS = frozenset({
    "get_event_loop_policy",
    "set_event_loop_policy",
})

# Classes deprecated in 3.14 (referenced as attributes or imported)
_POLICY_CLASSES = frozenset({
    "AbstractEventLoopPolicy",
    "DefaultEventLoopPolicy",
    "WindowsSelectorEventLoopPolicy",
    "WindowsProactorEventLoopPolicy",
})

# All deprecated names combined (for import detection)
_ALL_POLICY_NAMES = _POLICY_FUNCTIONS | _POLICY_CLASSES


class AsyncioEventLoopPolicyRule(BaseRule):
    rule_id = "CPY070"
    title   = "asyncio event loop policy deprecated in 3.14, removed in 3.16"
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
            # from asyncio import get_event_loop_policy / AbstractEventLoopPolicy / …
            if isinstance(n, ast.ImportFrom) and n.module == "asyncio":
                for alias in n.names:
                    if alias.name in _ALL_POLICY_NAMES:
                        findings.append(
                            self._make(filename, alias.name, n.lineno, n.col_offset)
                        )

            # asyncio.get_event_loop_policy() / asyncio.set_event_loop_policy(...)
            if isinstance(n, ast.Call):
                func = n.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr in _POLICY_FUNCTIONS
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "asyncio"
                ):
                    findings.append(
                        self._make(filename, func.attr, n.lineno, n.col_offset)
                    )

            # asyncio.DefaultEventLoopPolicy / asyncio.AbstractEventLoopPolicy / …
            # (attribute access — covers both bare references and calls to classes)
            if (
                isinstance(n, ast.Attribute)
                and n.attr in _POLICY_CLASSES
                and isinstance(n.value, ast.Name)
                and n.value.id == "asyncio"
            ):
                findings.append(
                    self._make(filename, n.attr, n.lineno, n.col_offset)
                )

        # Deduplicate by (line, col)
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, name: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename, line=line, col=col,
            rule_id=self.rule_id, title=self.title,
            description=(
                f"'asyncio.{name}' is part of the asyncio event loop policy "
                "system, which was deprecated in Python 3.14 and is scheduled "
                "for removal in Python 3.16 (gh-127949). "
                "The deprecated names are: get_event_loop_policy(), "
                "set_event_loop_policy(), AbstractEventLoopPolicy, "
                "DefaultEventLoopPolicy, WindowsSelectorEventLoopPolicy, "
                "and WindowsProactorEventLoopPolicy."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            affected_until="3.16",
            suggestion=(
                "Replace policy-based event loop management with asyncio.run() "
                "or asyncio.Runner(loop_factory=MyLoop). "
                "For example: asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)"
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html#deprecated",
        )
