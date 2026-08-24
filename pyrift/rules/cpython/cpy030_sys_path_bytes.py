"""
CPY030 — sys.path no longer accepts bytes entries in Python 3.11
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since Python 3.11, bytes objects are no longer accepted on sys.path.
Support broke between Python 3.2 and 3.6 with no one noticing until
after Python 3.10.0. Adding bytes to sys.path silently fails or
raises TypeError on newer versions.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class SysPathBytesRule(BaseRule):
    rule_id = "CPY030"
    title   = "sys.path no longer accepts bytes entries in Python 3.11+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Detect sys.path.append(b'...') or sys.path.insert(0, b'...')
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in ("append", "insert", "extend"):
                continue
            if not (isinstance(func.value, ast.Attribute) and
                    func.value.attr == "path" and
                    isinstance(func.value.value, ast.Name) and
                    func.value.value.id == "sys"):
                continue

            # Check if any argument is a bytes literal
            all_args = list(n.args)
            for arg in all_args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, bytes):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "A bytes object is being added to sys.path. "
                            "Since Python 3.11, bytes are no longer accepted "
                            "on sys.path. This silently failed between "
                            "Python 3.2 and 3.10 — on 3.11+ it raises TypeError."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.11",
                        suggestion=(
                            "Use a str instead of bytes for sys.path entries: "
                            "sys.path.append('/path/to/module') not b'/path/to/module'."
                        ),
                        docs_url=(
                            "https://docs.python.org/3/whatsnew/3.11.html"
                        ),
                    ))

        return findings