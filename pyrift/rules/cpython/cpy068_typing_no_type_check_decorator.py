"""
CPY068 — typing.no_type_check_decorator deprecated 3.13, removed 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``typing.no_type_check_decorator`` was deprecated in Python 3.13
(gh-106309, commit 32718f908cc) because, after eight years in the typing
module, it had never been supported by any major type checker.  A
``DeprecationWarning`` fires when the decorator is *applied* (not merely
imported).  The function was removed entirely in Python 3.15 (gh-133601,
commit e09837fcbf), so ``from typing import no_type_check_decorator``
raises ``ImportError`` on 3.15+.

``typing_extensions`` previously re-exported ``no_type_check_decorator``
but dropped it to maintain 3.15 compatibility (Redhat Bugzilla #2416981).

Detects:
  from typing import no_type_check_decorator
  from typing_extensions import no_type_check_decorator
  @typing.no_type_check_decorator
  @typing_extensions.no_type_check_decorator

Evidence:
  - Deprecated 3.13: https://github.com/python/cpython/issues/106309
  - Removed  3.15: https://github.com/python/cpython/issues/133601
  - Whatsnew: https://docs.python.org/3/whatsnew/3.15.html#removed
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_TYPING_MODULES = frozenset({"typing", "typing_extensions"})


class TypingNoTypeCheckDecoratorRule(BaseRule):
    rule_id = "CPY068"
    title   = "typing.no_type_check_decorator deprecated in 3.13, removed in 3.15"
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
            # from typing import no_type_check_decorator
            # from typing_extensions import no_type_check_decorator
            if (
                isinstance(n, ast.ImportFrom)
                and n.module in _TYPING_MODULES
            ):
                for alias in n.names:
                    if alias.name == "no_type_check_decorator":
                        findings.append(Finding(
                            file=filename, line=n.lineno, col=n.col_offset,
                            rule_id=self.rule_id, title=self.title,
                            description=(
                                f"'{n.module}.no_type_check_decorator' was "
                                "deprecated in Python 3.13 (DeprecationWarning "
                                "fires when the decorator is applied) and was "
                                "removed in Python 3.15.  Importing it raises "
                                "ImportError on Python 3.15+."
                            ),
                            severity=Severity.WARNING,
                            runtime=Runtime.CPYTHON,
                            affected_from="3.13",
                            suggestion=(
                                "Use typing.no_type_check() directly as a "
                                "decorator on the function you want to suppress "
                                "type checking for, or use "
                                "if typing.TYPE_CHECKING: blocks instead."
                            ),
                            docs_url="https://docs.python.org/3/whatsnew/3.15.html#removed",
                        ))

            # @typing.no_type_check_decorator  /  @typing_extensions.no_type_check_decorator
            if (
                isinstance(n, ast.Attribute)
                and n.attr == "no_type_check_decorator"
                and isinstance(n.value, ast.Name)
                and n.value.id in _TYPING_MODULES
            ):
                findings.append(Finding(
                    file=filename, line=n.lineno, col=n.col_offset,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        f"'{n.value.id}.no_type_check_decorator' was deprecated "
                        "in Python 3.13 (raises DeprecationWarning when applied) "
                        "and removed in Python 3.15.  On 3.15+ this raises "
                        "AttributeError at runtime."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "Use typing.no_type_check() directly as a decorator "
                        "on the function you want to suppress type checking for, "
                        "or use if typing.TYPE_CHECKING: blocks instead."
                    ),
                    docs_url="https://docs.python.org/3/whatsnew/3.15.html#removed",
                ))

        # Deduplicate by (line, col) to avoid double-reporting when both
        # an import and an attribute-access appear in the same file.
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique
