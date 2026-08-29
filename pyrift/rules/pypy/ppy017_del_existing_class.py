"""
PPY017 — Adding __del__ to existing class not called on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On PyPy, if you add a __del__ method to an existing class after
it has already been defined, the __del__ will NOT be called.
PyPy emits a RuntimeWarning. On CPython, this works silently.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class DelExistingClassRule(BaseRule):
    rule_id = "PPY017"
    title   = "Adding __del__ to existing class not called on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Detect: ClassName.__del__ = something
            if not isinstance(n, ast.Assign):
                continue
            for target in n.targets:
                if (isinstance(target, ast.Attribute) and
                        target.attr == "__del__"):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "A __del__ method is being assigned to an existing "
                            "class after definition. On PyPy, __del__ added to "
                            "an existing class will NOT be called — PyPy emits "
                            "a RuntimeWarning. On CPython, this works as expected. "
                            "This is a silent behaviour difference."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Define __del__ directly in the class body at "
                            "class definition time. Replacing or overriding "
                            "a __del__ that already exists works fine — "
                            "only adding it to a class that had none does not."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                            "#differences-related-to-garbage-collection-strategies"
                        ),
                    ))

        return findings