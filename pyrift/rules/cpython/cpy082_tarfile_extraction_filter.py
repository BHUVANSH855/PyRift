"""
CPY082 -- tarfile extraction without filter= (security, 3.12+)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Calling ``TarFile.extract()``, ``TarFile.extractall()``, or
``TarFile.extractfile()`` without an explicit ``filter=`` argument is
deprecated since Python 3.12 and will change its default from
``'fully_trusted'`` to ``'data'`` in a future version.

The ``'fully_trusted'`` default allows extracted files to overwrite
arbitrary paths on the filesystem (a path traversal / "zip slip"
vulnerability).

    tf.extractall(path)                     # unsafe default, deprecated
    tf.extract(member, path)                # unsafe default, deprecated
    tf.extractall(path, filter='data')      # safe
    tf.extractall(path, filter='tar')       # explicit (less safe)
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_EXTRACT_METHODS = frozenset({"extract", "extractall", "extractfile"})


class TarfileExtractionFilterRule(BaseRule):
    rule_id = "CPY082"
    title = "tarfile extraction without filter= is a security risk (deprecated 3.12)"
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
            if func.attr not in _EXTRACT_METHODS:
                continue
            # skip if filter= keyword already present
            if any(kw.arg == "filter" for kw in n.keywords):
                continue
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"TarFile.{func.attr}() called without 'filter=' "
                    "argument. The default 'fully_trusted' filter allows "
                    "extracted files to overwrite arbitrary paths "
                    "(path traversal / zip-slip vulnerability). "
                    "This was deprecated in Python 3.12 and the default "
                    "will change to 'data' in a future release."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.12",
                suggestion=(
                    "Add filter='data' for safe extraction of "
                    "untrusted archives, or filter='tar' to preserve "
                    "tar-specific features while still logging warnings. "
                    "Only use filter='fully_trusted' for archives you "
                    "control entirely."
                ),
                docs_url=(
                    "https://docs.python.org/3/library/tarfile.html"
                    "#extraction-filters"
                ),
            ))
        return findings