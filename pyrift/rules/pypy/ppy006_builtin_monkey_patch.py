"""
PPY006 — Monkey-patching built-in types behaves differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, adding attributes to built-in types like list, dict,
str raises TypeError. On PyPy, the same operation may succeed but
may not behave as expected due to how PyPy's JIT optimises built-in
types.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

BUILTIN_TYPES = {
    "list", "dict", "str", "int", "float", "tuple",
    "set", "frozenset", "bytes", "bytearray", "bool",
}


class BuiltinMonkeyPatchRule(BaseRule):
    rule_id = "PPY006"
    title   = "Monkey-patching built-in types behaves differently on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Detect: list.method = something  or  dict.attr = something
            if not isinstance(n, ast.Assign):
                continue

            for target in n.targets:
                if not isinstance(target, ast.Attribute):
                    continue
                obj = target.value
                if isinstance(obj, ast.Name) and obj.id in BUILTIN_TYPES:
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"Attempting to monkey-patch built-in type "
                            f"'{obj.id}' by setting '{obj.id}.{target.attr}'. "
                            "On CPython this raises TypeError. On PyPy, the "
                            "JIT compiler makes aggressive assumptions about "
                            "built-in types — patching them may not behave "
                            "as expected or may bypass JIT optimisations "
                            "without any error."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Subclass the built-in type instead of patching it: "
                            f"class My{obj.id.capitalize()}({obj.id}): ... "
                            "This works correctly on both CPython and PyPy."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                        ),
                    ))

        return findings