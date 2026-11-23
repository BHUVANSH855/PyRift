"""
CPY086 -- os.popen() and os.spawn*() soft-deprecated (3.14)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``os.popen()`` and the ``os.spawn*()`` family of functions were
soft-deprecated in Python 3.14. The ``subprocess`` module is the
recommended replacement for all process management.

    os.popen('ls')                            # soft-deprecated 3.14
    os.spawnl(os.P_WAIT, path, *args)        # soft-deprecated 3.14
    subprocess.run(['ls'], capture_output=True)  # correct
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_SPAWN_FUNCS = frozenset({
    "spawnl", "spawnle", "spawnlp", "spawnlpe",
    "spawnv", "spawnve", "spawnvp", "spawnvpe",
})


class OsPopenSpawnRule(BaseRule):
    rule_id = "CPY086"
    title = "os.popen() and os.spawn*() soft-deprecated in Python 3.14"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not isinstance(func, ast.Attribute):
                continue
            if not (isinstance(func.value, ast.Name) and func.value.id == "os"):
                continue
            attr = func.attr
            if attr != "popen" and attr not in _SPAWN_FUNCS:
                continue
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"os.{attr}() was soft-deprecated in Python 3.14. "
                    "The subprocess module provides a safer, more "
                    "powerful interface for process management."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.14",
                suggestion=(
                    "Replace os.popen() with subprocess.run() or "
                    "subprocess.Popen(). Replace os.spawn*() with "
                    "subprocess.run() or subprocess.Popen() with "
                    "appropriate arguments."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/subprocess.html"
                ),
            ))
        return findings