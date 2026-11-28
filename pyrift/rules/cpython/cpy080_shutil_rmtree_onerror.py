"""
CPY080 -- shutil.rmtree(onerror=...) deprecated in 3.12, no removal date yet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``onerror`` keyword argument to ``shutil.rmtree()`` was deprecated in
Python 3.12 when the ``onexc`` parameter was introduced. No specific removal
version has been scheduled; it appears in the "pending removal in future
versions" list in the Python docs.

    shutil.rmtree(path, onerror=handler)   # deprecated 3.12, use onexc=
    shutil.rmtree(path, onexc=handler)     # correct

Note: the callback signature differs — ``onexc`` receives the live exception
object as the third argument, while ``onerror`` received the ``sys.exc_info()``
tuple.
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class ShutilRmtreeOnErrorRule(BaseRule):
    rule_id = "CPY080"
    title = "shutil.rmtree(onerror=...) deprecated in 3.12, use onexc= instead"
    runtime = "cpython"
    severity = Severity.WARNING

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
                    "was deprecated in Python 3.12 when 'onexc' was "
                    "introduced. No specific removal version has been "
                    "scheduled, but using 'onerror=' emits a "
                    "DeprecationWarning on Python 3.12+."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.12",
                suggestion=(
                    "Replace 'onerror=' with 'onexc='. The callback "
                    "signature changes: the third argument becomes the "
                    "live exception object rather than the "
                    "sys.exc_info() tuple."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/shutil.html"
                    "#shutil.rmtree"
                ),
            ))
        return findings