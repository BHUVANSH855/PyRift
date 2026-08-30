"""
CPY064 — Deprecated AST node types removed in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.13 deprecated ast.Num, ast.Str, ast.Bytes, ast.NameConstant,
ast.Ellipsis, ast.Index, and ast.ExtSlice (PEP 3120 / GH-90953).
Python 3.14 removes them entirely. Code that references these classes
(e.g. isinstance(x, ast.Num)) will raise AttributeError on 3.14+.

Detects:
  isinstance(x, ast.Num)
  isinstance(x, ast.Str)
  isinstance(x, ast.Bytes)
  isinstance(x, ast.NameConstant)
  isinstance(x, ast.Ellipsis)
  ast.Num in some_list
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_DEPRECATED_AST_NODES = {
    "Num", "Str", "Bytes", "NameConstant", "Ellipsis", "Index", "ExtSlice",
}


class AstDeprecatedNodesRule(BaseRule):
    rule_id = "CPY064"
    title   = "Deprecated AST node types removed in Python 3.14"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # ast.Num — Attribute access pattern: ast.Num, ast.Str, etc.
            if (isinstance(n, ast.Attribute)
                    and isinstance(n.value, ast.Name)
                    and n.value.id == "ast"
                    and n.attr in _DEPRECATED_AST_NODES):
                findings.append(self._make(filename, n.attr, n.lineno, n.col_offset))

        # Deduplicate by (line, col)
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _make(self, filename: str, node_name: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename,
            line=line,
            col=col,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                f"References deprecated AST node type 'ast.{node_name}'. "
                "These node types were deprecated in Python 3.13 and removed "
                "in Python 3.14. Code using them raises AttributeError on 3.14+."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                f"Replace ast.{node_name} with the modern equivalent: "
                "ast.Constant for Num/Str/Bytes/NameConstant/Ellipsis, "
                "ast.Subscript for Index, ast.Subscript for ExtSlice."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html",
        )