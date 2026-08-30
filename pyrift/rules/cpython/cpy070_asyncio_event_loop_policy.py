"""
CPY070 — asyncio event loop policy deprecated in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.14 deprecates the event loop policy system:
  - asyncio.get_event_loop_policy()
  - asyncio.set_event_loop_policy()
  - asyncio.DefaultEventLoopPolicy
These will be removed in a future version. Use asyncio.run() or
asyncio.Runner() instead.

Detects:
  asyncio.get_event_loop_policy()
  asyncio.set_event_loop_policy(...)
  asyncio.DefaultEventLoopPolicy
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_POLICY_FUNCTIONS = {"get_event_loop_policy", "set_event_loop_policy"}


class AsyncioEventLoopPolicyRule(BaseRule):
    rule_id = "CPY070"
    title   = "asyncio event loop policy deprecated in Python 3.14"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # asyncio.get_event_loop_policy() / asyncio.set_event_loop_policy(...)
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Attribute)
                        and func.attr in _POLICY_FUNCTIONS
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "asyncio"):
                    findings.append(self._make(filename, func.attr, n.lineno, n.col_offset))

            # asyncio.DefaultEventLoopPolicy (attribute access, not call)
            if (isinstance(n, ast.Attribute)
                    and n.attr == "DefaultEventLoopPolicy"
                    and isinstance(n.value, ast.Name)
                    and n.value.id == "asyncio"):
                findings.append(self._make(filename, "DefaultEventLoopPolicy", n.lineno, n.col_offset))

        # Deduplicate
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
                f"asyncio.{name} is deprecated since Python 3.14. "
                "The event loop policy system will be removed in a future version. "
                "Use asyncio.run() or asyncio.Runner() for event loop management."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Replace policy-based event loop management with asyncio.run() "
                "or asyncio.Runner(). For custom loop configuration, pass "
                "parameters directly to asyncio.run()."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html",
        )
