"""
pyrift.base_rule
~~~~~~~~~~~~~~~~
Every rule inherits from BaseRule.
"""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .finding import Finding, Severity

if TYPE_CHECKING:  # pragma: no cover
    from .targets import TargetConfig


class BaseRule(ABC):
    """Abstract base class for all pyrift rules."""

    rule_id: str = ""
    title: str = ""
    runtime: str = "both"
    category: str = "compatibility"
    severity: Severity = Severity.WARNING

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Guard against accidental instance-level state in rule subclasses.

        ``ALL_RULES`` in :mod:`pyrift.scanner` holds a single shared instance
        of every rule, reused across all files and scans.  An ``__init__``
        override in a rule subclass that stores per-call results in ``self``
        would bleed across invocations, producing incorrect findings.

        Raise ``TypeError`` at class-definition time (import time) so the
        problem is caught immediately rather than silently at scan time.
        Use ``ClassVar`` attributes for read-only rule-level configuration.
        """
        super().__init_subclass__(**kwargs)
        if "__init__" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__}: BaseRule subclasses must not define "
                f"__init__.  ALL_RULES reuses a single instance per rule "
                f"across all scans; instance state introduced in __init__ "
                f"will bleed across files.  Use class-level ClassVar "
                f"attributes for read-only configuration instead."
            )

    @abstractmethod
    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        """
        Run the rule against *node*.

        ``target_config`` contains optional project target information such
        as supported Python versions and target platform.

        Return a possibly empty list of findings.
        """
        ...  # pragma: no cover