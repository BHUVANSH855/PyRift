"""
CPY080 -- shutil.rmtree(onerror=...) deprecated (3.12), removed (3.14)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``onerror`` keyword argument to ``shutil.rmtree()`` was deprecated in
Python 3.12 and removed in Python 3.14. Use ``onexc=`` instead.

    shutil.rmtree(path, onerror=handler)   # deprecated 3.12, removed 3.14
    shutil.rmtree(path, onexc=handler)     # correct
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ShutilRmtreeOnErrorRule(BaseRule):
    rule_id = "CPY080"
    title = "shutil.rmtree(onerror=...) removed in 3.14, use onexc="
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for call in collect_calls(node, "rmtree", module="shutil"):
            if "onerror" not in call.kwargs:
                continue
            findings.append(Finding(
                file=filename,
                line=call.line,
                col=call.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "The 'onerror' keyword argument to shutil.rmtree() "
                    "was deprecated in Python 3.12 and removed in "
                    "Python 3.14. Calling it with onerror= raises "
                    "TypeError on Python 3.14+."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.12",
                affected_until="3.14",
                suggestion=(
                    "Replace 'onerror=' with 'onexc='. The callback "
                    "signature changes from (func, path, exc_info) to "
                    "(func, path, exc) where exc is the exception "
                    "instance rather than the sys.exc_info() tuple."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/shutil.html"
                    "#shutil.rmtree"
                ),
            ))
        return findings