"""
PPY025 — Set ordering differs between CPython and PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, sets are unordered — iteration order is not guaranteed.
On PyPy, sets maintain insertion order (PyPy's own documentation:
"Dictionaries and sets are ordered on PyPy"). Code that depends on set
iteration order may produce different results across runtimes.

Framing (2026-09 audit item #19): neither runtime gives set iteration
a stable *language-level* ordering contract -- PyPy's ordering is a
PyPy-specific implementation behavior, not a portable guarantee any
more than CPython's lack of ordering is. The finding is framed around
that portability principle ("your code depends on set order, which is
undefined") rather than "PyPy differs from CPython", per the review.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class SetOrderingRule(BaseRule):
    rule_id = "PPY025"
    title   = "Set iteration order differs between CPython and PyPy"
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
            # Detect: list(set), tuple(set), frozenset iteration
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Name) and
                        func.id in ("list", "tuple") and
                        n.args):
                    arg = n.args[0]
                    if isinstance(arg, ast.Set):
                        findings.append(self._make_call_finding(
                            filename, n, func.id, arg))

                # Detect: next(iter(set_var))
                if (isinstance(func, ast.Name) and
                        func.id == "next" and
                        n.args and
                        isinstance(n.args[0], ast.Call)):
                    inner = n.args[0]
                    inner_func = inner.func
                    if (isinstance(inner_func, ast.Name) and
                            inner_func.id == "iter" and
                            inner.args and
                            isinstance(inner.args[0], (ast.Set, ast.Name))):
                        findings.append(self._make_finding(
                            filename, n,
                            "next(iter(s)) on a set"))

            # Detect: for x in {1, 2, 3} (literal set only)
            # ast.Name is too broad — any variable could be a set
            if (isinstance(n, ast.For)
                    and isinstance(n.iter, ast.Set)):
                findings.append(self._make_finding(
                    filename, n,
                    "for-loop over a set literal"))

        return findings

    def _make_finding(
        self, filename: str, node: ast.AST, context: str,
    ) -> Finding:
        return Finding(
            file=filename,
            line=node.lineno,  # type: ignore[attr-defined]
            col=node.col_offset,  # type: ignore[attr-defined]
            rule_id=self.rule_id,
            title=self.title,
            description=(
                f"{context} depends on set iteration order, which is "
                "not part of the Python language's set contract on "
                "either runtime -- CPython's sets remain unordered "
                "even in current versions, while PyPy's sets are "
                "documented as maintaining insertion order (PyPy's own "
                "docs: \"Dictionaries and sets are ordered on PyPy\"). "
                "Relying on either behavior, rather than treating set "
                "order as genuinely undefined, is what makes this code "
                "non-portable."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.PYPY,
            suggestion=(
                "Use sorted(your_set) if you need a "
                "deterministic order — this works correctly "
                "on both CPython and PyPy."
            ),
            docs_url=(
                "https://doc.pypy.org/en/latest/"
                "cpython_differences.html#miscellaneous"
            ),
        )

    def _make_call_finding(
        self, filename: str, node: ast.Call, func_name: str, arg: ast.AST,
    ) -> Finding:
        if isinstance(arg, ast.Set):
            source = f"{func_name}({{...}})"
        elif isinstance(arg, ast.Name):
            source = f"{func_name}({arg.id})"
        else:
            source = f"{func_name}(set)"
        return Finding(
            file=filename,
            line=node.lineno,
            col=node.col_offset,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                f"Converting a set with {source} depends on set "
                "iteration order, which is not part of the Python "
                "language's set contract on either runtime -- "
                "CPython's sets remain unordered even in current "
                "versions, while PyPy's sets are documented as "
                "maintaining insertion order. Relying on either "
                "behavior, rather than treating set order as "
                "genuinely undefined, is what makes this code "
                "non-portable."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.PYPY,
            suggestion=(
                "Use sorted(your_set) if you need a "
                "deterministic order — this works correctly "
                "on both CPython and PyPy."
            ),
            docs_url=(
                "https://doc.pypy.org/en/latest/"
                "cpython_differences.html#miscellaneous"
            ),
        )