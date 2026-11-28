"""
CPY082 -- tarfile extraction without filter= (deprecated 3.12–3.13)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Calling ``TarFile.extract()`` or ``TarFile.extractall()`` without an explicit
``filter=`` argument emits a ``DeprecationWarning`` on Python 3.12 and 3.13.
In Python 3.14 the default changed to ``'data'`` and the warning was removed.

The old ``'fully_trusted'`` default allowed extracted files to overwrite
arbitrary paths on the filesystem (path traversal / "zip slip", CVE-2007-4559).

    tf.extractall(path)                     # DeprecationWarning on 3.12–3.13
    tf.extract(member, path)                # DeprecationWarning on 3.12–3.13
    tf.extractall(path, filter='data')      # safe, explicit
    tf.extractall(path, filter='tar')       # explicit (less safe)

Note: ``extractfile()`` has no ``filter=`` parameter — it returns a file-like
object and never writes to disk.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_EXTRACT_METHODS = frozenset({"extract", "extractall"})


class TarfileExtractionFilterRule(BaseRule):
    rule_id = "CPY082"
    title = "tarfile extraction without filter= deprecated 3.12–3.13 (CVE-2007-4559)"
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
                    "argument. On Python 3.12–3.13 this emits a "
                    "DeprecationWarning because the default "
                    "'fully_trusted' filter allows extracted files to "
                    "overwrite arbitrary paths (path traversal / "
                    "zip-slip, CVE-2007-4559). In Python 3.14 the "
                    "default changed to 'data'."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.12",
                affected_until="3.13",
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