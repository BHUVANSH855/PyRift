"""
PPY055 -- sys.setprofile() / sys.getprofile() not supported on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyPy's JIT compiler optimises call graphs in ways that prevent every
call/return event from being delivered to the profile function installed
via sys.setprofile(). Profiling tools that rely on this hook will produce
incomplete results or silently see no events on PyPy.

Documentation:
  https://doc.pypy.org/en/latest/cpython_differences.html#profiling
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_PROFILE_FUNCS = frozenset({"setprofile", "getprofile"})


class SysSetprofileRule(BaseRule):
    rule_id = "PPY055"
    title = "sys.setprofile() / sys.getprofile() not reliably supported on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for func_name in _PROFILE_FUNCS:
            for call_info in collect_calls(node, func_name, module="sys"):
                findings.append(Finding(
                    file=filename,
                    line=call_info.line,
                    col=call_info.col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"sys.{func_name}() is part of CPython's profiling "
                        "hook API. On PyPy, the JIT compiler optimises call "
                        "graphs in ways that prevent every call/return event "
                        "from being delivered to the profile function. "
                        "Profiling tools that rely on this hook will produce "
                        "incomplete results or silently see no events on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "For profiling on PyPy, use vmprof "
                        "(https://vmprof.readthedocs.io/) which is designed "
                        "to work with PyPy's JIT, or use pypyjit.set_param() "
                        "to control JIT thresholds before benchmarking."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#profiling"
                    ),
                ))
        return findings
