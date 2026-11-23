"""
CPY084 -- urllib.request.URLopener / FancyURLopener removed (3.14)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``urllib.request.URLopener`` and ``urllib.request.FancyURLopener`` were
deprecated in Python 3.3 and removed in Python 3.14. They raise
``ImportError`` or ``AttributeError`` on 3.14+.

    from urllib.request import URLopener       # removed 3.14
    from urllib.request import FancyURLopener  # removed 3.14
    urllib.request.URLopener()                 # removed 3.14
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED = frozenset({"URLopener", "FancyURLopener"})


class UrllibUrlopenDeprecatedRule(BaseRule):
    rule_id = "CPY084"
    title = "urllib.request.URLopener / FancyURLopener removed in Python 3.14"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for info in collect_imports(node).imports:
            mod = info.module or ""
            name = info.name or ""
            if mod == "urllib.request" and name in _REMOVED:
                findings.append(Finding(
                    file=filename,
                    line=info.line,
                    col=info.col,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"'urllib.request.{name}' was deprecated in "
                        "Python 3.3 and removed in Python 3.14. "
                        "Importing it raises ImportError on 3.14+."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.14",
                    suggestion=(
                        "Use urllib.request.urlopen() for simple URL "
                        "fetching, or the third-party 'requests' or "
                        "'httpx' libraries for more complex use cases."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.14.html"
                        "#removed"
                    ),
                ))
        return findings