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
    title = "Adding __del__ to existing class not called on PyPy"
    runtime = "pypy"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        # Collect class names defined in the analyzed AST.  We only flag
        # assignments where the receiver is statically known to be a class.
        class_names = {
            class_node.name
            for class_node in ast.walk(node)
            if isinstance(class_node, ast.ClassDef)
        }

        for assignment in ast.walk(node):
            if not isinstance(assignment, ast.Assign):
                continue

            for target in assignment.targets:
                if not (
                    isinstance(target, ast.Attribute)
                    and target.attr == "__del__"
                    and isinstance(target.value, ast.Name)
                    and target.value.id in class_names
                ):
                    continue

                findings.append(
                    Finding(
                        file=filename,
                        line=assignment.lineno,
                        col=assignment.col_offset,
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
                            "https://doc.pypy.org/en/latest/"
                            "cpython_differences.html"
                            "#differences-related-to-garbage-collection-strategies"
                        ),
                    )
                )

        return findings