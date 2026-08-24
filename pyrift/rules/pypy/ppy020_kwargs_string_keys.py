"""
PPY020 — dict(**{non_string_key: val}) raises TypeError on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython 2.7, dict() and dict.update() accepted non-string keys
when passed as **kwargs. On PyPy (and CPython 3.x), dictionaries
passed as **kwargs must have only string keys — non-string keys
raise TypeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class KwargsStringKeysRule(BaseRule):
    rule_id = "PPY020"
    title   = "dict(**kwargs) requires string keys on PyPy and Python 3"
    runtime = "both"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            for kw in n.keywords:
                if kw.arg is not None:
                    continue  # not **unpacking
                if not isinstance(kw.value, ast.Dict):
                    continue
                for key in kw.value.keys:
                    if key is None:
                        continue
                    if not isinstance(key, ast.Constant):
                        continue
                    if not isinstance(key.value, str):
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                f"A non-string key ({key.value!r}) "
                                "is used in a dict passed as **kwargs. "
                                "On PyPy and CPython 3.x, this raises "
                                "TypeError. Only string keys are allowed "
                                "in **kwargs."
                            ),
                            severity=Severity.ERROR,
                            runtime=Runtime.BOTH,
                            suggestion=(
                                "Ensure all keys in **kwargs dicts "
                                "are strings. Use positional arguments "
                                "or a regular dict argument instead "
                                "of **unpacking with non-string keys."
                            ),
                            docs_url=(
                                "https://doc.pypy.org/en/latest/"
                                "cpython_differences.html#miscellaneous"
                            ),
                        ))

        return findings