"""
pyrift.base_rule
~~~~~~~~~~~~~~~~
Every rule inherits from BaseRule.
"""
from __future__ import annotations
import ast
from abc import ABC, abstractmethod
from .finding import Finding


class BaseRule(ABC):
    """Abstract base for all pyrift rules."""

    rule_id: str = ""
    title:   str = ""
    runtime: str = "both"

    @abstractmethod
    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        """
        Run the rule against *node*.
        Return a (possibly empty) list of Finding objects.
        """
        ...