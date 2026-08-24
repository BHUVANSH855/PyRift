"""
PPY027 — Deleting module/class attributes is slower on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On PyPy, module and class dictionaries are optimised under the
assumption that deleting attributes is rare. Deleting attributes
from modules or classes is significantly slower on PyPy than on
CPython. Code that frequently deletes module-level attributes in
hot paths will silently degrade performance on PyPy.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class ModuleAttrDeleteRule(BaseRule):
    rule_id = "PPY027"
    title   = "Deleting module/class attributes is significantly slower on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Delete):
                continue
            for target in n.targets:
                if isinstance(target, ast.Attribute):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"Attribute '{target.attr}' is being deleted. "
                            "On PyPy, module and class dictionaries are "
                            "optimised under the assumption that deleting "
                            "attributes is rare. Frequent attribute deletion "
                            "is significantly slower on PyPy than on CPython "
                            "and will silently degrade performance in hot paths."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Avoid frequent attribute deletion in hot code paths. "
                            "Set attributes to None instead of deleting them, "
                            "or restructure code to avoid deletion entirely."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                            "#miscellaneous"
                        ),
                    ))
        return findings