"""
PPY057 -- copyreg.dispatch_table / pickle.dispatch_table behaves differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, Pickler accesses copyreg.dispatch_table live. On PyPy's
pure-Python pickle implementation, the table may be read at a different time,
so mutations mid-stream produce different results than on CPython.

Documentation:
  https://doc.pypy.org/en/latest/cpython_differences.html
  https://docs.python.org/3/library/copyreg.html#copyreg.dispatch_table
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


def _is_dispatch_table_mutation(node: ast.stmt) -> tuple[bool, str]:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "dispatch_table"
                and isinstance(target.value, ast.Name)
                and target.value.id in ("copyreg", "pickle")
            ):
                return True, f"{target.value.id}.dispatch_table"
            if isinstance(target, ast.Subscript):
                val = target.value
                if (
                    isinstance(val, ast.Attribute)
                    and val.attr == "dispatch_table"
                    and isinstance(val.value, ast.Name)
                    and val.value.id in ("copyreg", "pickle")
                ):
                    return True, f"{val.value.id}.dispatch_table"
    # copyreg.dispatch_table.update(...)
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        call = node.value
        if isinstance(call.func, ast.Attribute) and call.func.attr in ("update", "clear", "pop"):
            obj = call.func.value
            if (
                isinstance(obj, ast.Attribute)
                and obj.attr == "dispatch_table"
                and isinstance(obj.value, ast.Name)
                and obj.value.id in ("copyreg", "pickle")
            ):
                return True, f"{obj.value.id}.dispatch_table"
    return False, ""


class CopyregDispatchTableRule(BaseRule):
    rule_id = "PPY057"
    title = "copyreg.dispatch_table / pickle.dispatch_table mutation differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            for stmt in ast.walk(n) if isinstance(n, ast.Module) else []:
                is_mutation, table_name = _is_dispatch_table_mutation(stmt)
                if not is_mutation:
                    continue
                findings.append(Finding(
                    file=filename,
                    line=stmt.lineno,
                    col=stmt.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"Mutating {table_name} relies on CPython's C "
                        "implementation of Pickler reading the global "
                        "dispatch table live. PyPy's pure-Python pickle "
                        "may read the table at a different time, making "
                        "runtime-ordered mutations produce different results "
                        "than on CPython."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use the per-instance dispatch_table instead: "
                        "p = pickle.Pickler(f); "
                        "p.dispatch_table = copyreg.dispatch_table.copy(); "
                        "p.dispatch_table[MyClass] = my_reducer. "
                        "This avoids global state and works consistently "
                        "across runtimes."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/copyreg.html"
                        "#copyreg.dispatch_table"
                    ),
                ))
        return findings
