"""
CPY093 -- glob.glob0() / glob.glob1() removed (3.15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The private helper functions ``glob.glob0()`` and ``glob.glob1()`` were
never part of the public API but were accessible and used in some
third-party code.  They were removed in Python 3.15.

    glob.glob0(dirname, pattern)   # removed 3.15
    glob.glob1(dirname, pattern)   # removed 3.15
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED_FUNCS = frozenset({"glob0", "glob1"})


class GlobRemovedRule(BaseRule):
    rule_id = "CPY093"
    title = "glob.glob0() / glob.glob1() removed in Python 3.15"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for func_name in _REMOVED_FUNCS:
            for call in collect_calls(node, func_name, module="glob"):
                findings.append(Finding(
                    file=filename,
                    line=call.line,
                    col=call.col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"glob.{func_name}() was a private helper that was "
                        "never part of the public API and was removed in "
                        "Python 3.15."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.15",
                    suggestion=(
                        "Use glob.glob() with a full path pattern, or "
                        "os.listdir() with fnmatch.filter() for the same "
                        "effect as the removed helpers."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.15.html"
                        "#removed"
                    ),
                ))
        return findings