"""
CPY054 — int() no longer delegates to __trunc__() in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before Python 3.14, int() would call __trunc__() on objects that
did not implement __int__() or __index__(). In Python 3.14, this
delegation was removed. Custom numeric types relying on __trunc__()
for int() conversion can therefore break.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class IntTruncRule(BaseRule):
    rule_id = "CPY054"
    title = "int() no longer delegates to __trunc__() in Python 3.14"
    runtime = "cpython"
    severity = Severity.ERROR

    @staticmethod
    def _is_abstract_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Return whether a method has an @abstractmethod decorator."""
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Name)
                and decorator.id == "abstractmethod"
            ):
                return True

            if (
                isinstance(decorator, ast.Attribute)
                and decorator.attr == "abstractmethod"
            ):
                return True

        return False

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for class_node in ast.walk(node):
            if not isinstance(class_node, ast.ClassDef):
                continue

            methods = [
                child
                for child in class_node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]

            method_names = {method.name for method in methods}

            if "__trunc__" not in method_names:
                continue

            if "__int__" in method_names or "__index__" in method_names:
                continue

            trunc_methods = [
                method
                for method in methods
                if method.name == "__trunc__"
            ]

            # Abstract protocol methods describe an interface; they do
            # not by themselves establish a concrete int() compatibility
            # risk.
            if all(self._is_abstract_method(method) for method in trunc_methods):
                continue

            trunc_node = trunc_methods[0]

            findings.append(
                Finding(
                    file=filename,
                    line=trunc_node.lineno,
                    col=trunc_node.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "__trunc__() is defined without a corresponding "
                        "__int__() or __index__() method in this class. "
                        "Before Python 3.14, int() could delegate to "
                        "__trunc__() in this situation. Python 3.14 "
                        "removed that delegation, so int(obj) can now "
                        "raise TypeError."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.14",
                    suggestion=(
                        "Implement __int__() or __index__() instead of "
                        "relying on int() delegating to __trunc__()."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.14.html"
                        "#changes-in-the-python-api"
                    ),
                )
            )

        return findings
