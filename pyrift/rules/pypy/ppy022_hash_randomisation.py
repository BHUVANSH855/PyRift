"""
PPY022 — Hash randomisation (-R flag) ignored on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, the -R flag and PYTHONHASHSEED environment variable
control hash randomisation. On PyPy, -R is ignored — PyPy always
uses the SipHash algorithm with randomisation. Code that sets
PYTHONHASHSEED=0 expecting deterministic hashes may behave
differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class HashRandomisationRule(BaseRule):
    rule_id = "PPY022"
    title   = "PYTHONHASHSEED=0 does not disable hash randomisation on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # Detect os.environ['PYTHONHASHSEED'] or os.getenv('PYTHONHASHSEED')
            if (
                isinstance(n, ast.Subscript)
                and isinstance(n.value, ast.Attribute)
                and n.value.attr == "environ"
            ):
                slice_node = n.slice
                if isinstance(slice_node, ast.Constant) and slice_node.value == "PYTHONHASHSEED":
                    findings.append(self._make(filename, n))
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Attribute) and
                        func.attr == "getenv" and
                        n.args and
                        isinstance(n.args[0], ast.Constant) and
                        n.args[0].value == "PYTHONHASHSEED"):
                    findings.append(self._make(filename, n))
        return findings

    def _make(self, filename: str, n: ast.AST) -> Finding:
        return Finding(
            file=filename,
            line=n.lineno,  # type: ignore[attr-defined]
            col=n.col_offset,  # type: ignore[attr-defined]
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "PYTHONHASHSEED is being read. On CPython, setting "
                "PYTHONHASHSEED=0 disables hash randomisation for "
                "deterministic dict/set ordering in tests. On PyPy, "
                "hash randomisation is always active and PYTHONHASHSEED=0 "
                "has no effect — tests relying on deterministic hash "
                "order may fail silently on PyPy."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.PYPY,
            suggestion=(
                "Do not rely on PYTHONHASHSEED=0 for deterministic "
                "ordering. Use sorted() explicitly when order matters "
                "in tests, or use OrderedDict for guaranteed ordering."
            ),
            docs_url=(
                "https://doc.pypy.org/en/latest/cpython_differences.html"
                "#miscellaneous"
            ),
        )