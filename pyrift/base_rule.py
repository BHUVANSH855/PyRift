"""
pyrift.base_rule
~~~~~~~~~~~~~~~~
Every rule inherits from BaseRule.
"""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .finding import Finding, Runtime

if TYPE_CHECKING:
    from .targets import TargetConfig


class BaseRule(ABC):
    """Abstract base class for all pyrift rules."""

    rule_id: str = ""
    title: str = ""
    runtime: Runtime = Runtime.BOTH

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
        ...