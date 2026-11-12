"""
PPY022 — PYTHONHASHSEED does not provide deterministic hashes on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyPy's hash randomisation behaviour differs from CPython. Code that
reads PYTHONHASHSEED expecting deterministic hash behaviour can
therefore behave differently on PyPy.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class HashRandomisationRule(BaseRule):
    rule_id = "PPY022"
    title = "Hash values for the same input differ between CPython and PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    @staticmethod
    def _is_os_environ(node: ast.Subscript) -> bool:
        """Return whether *node* represents os.environ[...] access."""
        return (
            isinstance(node.value, ast.Attribute)
            and node.value.attr == "environ"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "os"
        )

    @staticmethod
    def _is_pythonhashseed_key(node: ast.Subscript) -> bool:
        """Return whether the subscript uses a literal PYTHONHASHSEED key."""
        return (
            isinstance(node.slice, ast.Constant)
            and node.slice.value == "PYTHONHASHSEED"
        )

    @staticmethod
    def _is_pythonhashseed_getenv(node: ast.Call) -> bool:
        """Return whether *node* is os.getenv('PYTHONHASHSEED', ...)."""
        return (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "getenv"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and bool(node.args)
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "PYTHONHASHSEED"
        )

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for current in ast.walk(node):
            if isinstance(current, ast.Subscript):
                # Only flag reads:
                #
                #     os.environ["PYTHONHASHSEED"]
                #
                # Do not flag writes:
                #
                #     os.environ["PYTHONHASHSEED"] = "0"
                if (
                    isinstance(current.ctx, ast.Load)
                    and self._is_os_environ(current)
                    and self._is_pythonhashseed_key(current)
                ):
                    findings.append(self._make(filename, current))

            elif isinstance(current, ast.Call) and self._is_pythonhashseed_getenv(
                current
            ):
                findings.append(self._make(filename, current))

        return findings

    def _make(self, filename: str, node: ast.AST) -> Finding:
        return Finding(
            file=filename,
            line=node.lineno,  # type: ignore[attr-defined]
            col=node.col_offset,  # type: ignore[attr-defined]
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "PYTHONHASHSEED is being read. While PYTHONHASHSEED=0 "
                "does produce deterministic hashes on both CPython and PyPy, "
                "the actual hash *values* for the same input differ between "
                "the two implementations. Code that hardcodes a specific "
                "expected hash value (e.g. in test assertions) will silently "
                "break when run on PyPy, even with PYTHONHASHSEED=0."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.PYPY,
            suggestion=(
                "Do not assert specific hash values in tests. "
                "Use sorted() explicitly when order matters. "
                "If you need a stable hash across implementations, "
                "use hashlib (e.g. hashlib.md5) instead of hash()."
            ),
            docs_url=(
                "https://doc.pypy.org/en/latest/cpython_differences.html"
                "#miscellaneous"
            ),
        )