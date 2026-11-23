"""
CPY088 -- sre_compile / sre_constants / sre_parse removed (3.15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The private implementation modules ``sre_compile``, ``sre_constants``,
and ``sre_parse`` were removed in Python 3.15. These were internal
implementation details of the ``re`` module and were never part of the
public API.

    import sre_compile    # removed 3.15
    import sre_constants  # removed 3.15
    import sre_parse      # removed 3.15
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED = frozenset({"sre_compile", "sre_constants", "sre_parse"})


class SreModulesRemovedRule(BaseRule):
    rule_id = "CPY088"
    title = "sre_compile / sre_constants / sre_parse removed in Python 3.15"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            mod = info.module or ""
            top = mod.split(".")[0]
            if top not in _REMOVED:
                continue
            findings.append(Finding(
                file=filename,
                line=info.line,
                col=info.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"'{mod}' is a private implementation module of "
                    "the 're' package that was removed in Python 3.15. "
                    "Importing it raises ModuleNotFoundError on 3.15+."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.15",
                suggestion=(
                    "Use only the public 're' module API. If you need "
                    "low-level regex internals, consider the 'regex' "
                    "third-party package which exposes a stable API."
                ),
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.15.html"
                    "#removed"
                ),
            ))
        return findings