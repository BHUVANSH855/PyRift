"""
CPY092 -- logging.warn() deprecated alias (use logging.warning())
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``logging.warn()`` has been a deprecated alias for ``logging.warning()``
since Python 2.7 and was finally removed in Python 3.13.  The same
applies to the ``warn()`` method on ``Logger`` instances.

    logging.warn("message")       # removed 3.13
    logger.warn("message")        # removed 3.13
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class LoggingWarnRule(BaseRule):
    rule_id = "CPY092"
    title = "logging.warn() removed in Python 3.13 — use logging.warning()"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        # Catch module-level: logging.warn(...)
        for call in collect_calls(node, "warn", module="logging"):
            findings.append(Finding(
                file=filename,
                line=call.line,
                col=call.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "logging.warn() was a deprecated alias for "
                    "logging.warning() and was removed in Python 3.13. "
                    "It has been deprecated since Python 2.7."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.12",
                affected_until="3.13",
                suggestion="Replace logging.warn(...) with logging.warning(...)",
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.13.html"
                    "#removed"
                ),
            ))

        # Also catch instance-level: logger.warn(...)
        # We look for any .warn() call that is NOT logging.warn()
        # (already caught above) by checking the attribute directly.
        for call_node in ast.walk(node):
            if not isinstance(call_node, ast.Call):
                continue
            func = call_node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "warn"):
                continue
            # Skip if it was already caught as logging.warn via collect_calls
            if isinstance(func.value, ast.Name) and func.value.id == "logging":
                continue
            # Only flag if the receiver looks like a Logger variable
            # (common names: logger, log, root_logger, app_logger, etc.)
            # We flag any .warn() call since the method was removed from
            # Logger instances in 3.13 too.
            findings.append(Finding(
                file=filename,
                line=call_node.lineno,
                col=call_node.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "Logger.warn() was a deprecated alias for "
                    "Logger.warning() and was removed in Python 3.13."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.12",
                affected_until="3.13",
                suggestion=(
                    "Replace <logger>.warn(...) with <logger>.warning(...)"
                ),
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.13.html"
                    "#removed"
                ),
            ))
        return findings