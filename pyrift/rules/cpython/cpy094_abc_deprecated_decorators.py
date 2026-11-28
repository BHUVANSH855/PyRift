"""
CPY094 -- abc.abstractclassmethod / abstractstaticmethod / abstractproperty
           raise DeprecationWarning in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Three deprecated decorators in the ``abc`` module now raise
``DeprecationWarning`` at **decoration time** in Python 3.14:

    @abc.abstractclassmethod  # DeprecationWarning since 3.3; now ERROR-level warn
    class Foo:
        @abc.abstractclassmethod
        def meth(cls): ...

    @abc.abstractstaticmethod  # same
    @abc.abstractproperty       # same

The replacements are:

    @classmethod
    @abc.abstractmethod
    def meth(cls): ...

    @staticmethod
    @abc.abstractmethod
    def meth(): ...

    @property
    @abc.abstractmethod
    def prop(self): ...

These three symbols were soft-deprecated since Python 3.3.  In 3.14 they
begin actively warning and are scheduled for removal in a future release.

Reference: https://docs.python.org/3/whatsnew/3.14.html#deprecated
CPython issue: https://github.com/python/cpython/issues/105268
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_DEPRECATED_NAMES = frozenset({
    "abstractclassmethod",
    "abstractstaticmethod",
    "abstractproperty",
})

_REPLACEMENTS = {
    "abstractclassmethod": "@classmethod + @abc.abstractmethod",
    "abstractstaticmethod": "@staticmethod + @abc.abstractmethod",
    "abstractproperty": "@property + @abc.abstractmethod",
}


def _extract_decorator_info(
    deco: ast.expr,
) -> tuple[str | None, str | None]:
    """Return (attr_name, qualifier) for a decorator node.

    For ``@abc.abstractclassmethod`` returns ("abstractclassmethod", "abc").
    For ``@abstractclassmethod`` returns ("abstractclassmethod", None).
    For anything else returns (None, None).
    """
    if isinstance(deco, ast.Name) and deco.id in _DEPRECATED_NAMES:
        return deco.id, None
    if (
        isinstance(deco, ast.Attribute)
        and deco.attr in _DEPRECATED_NAMES
        and isinstance(deco.value, ast.Name)
    ):
        return deco.attr, deco.value.id
    # @abc.abstractclassmethod(...) -- rare but possible
    if isinstance(deco, ast.Call):
        return _extract_decorator_info(deco.func)
    return None, None


class AbcDeprecatedDecoratorsRule(BaseRule):
    rule_id = "CPY094"
    title = "abc.abstractclassmethod / abstractstaticmethod / abstractproperty deprecated in 3.14"
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
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for deco in n.decorator_list:
                attr_name, qualifier = _extract_decorator_info(deco)
                if attr_name is None:
                    continue
                replacement = _REPLACEMENTS[attr_name]
                qualified = f"abc.{attr_name}" if qualifier == "abc" else attr_name
                findings.append(Finding(
                    file=filename,
                    line=deco.lineno,
                    col=deco.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"@{qualified} has been deprecated since Python 3.3 "
                        "and now raises DeprecationWarning at decoration time "
                        "in Python 3.14. It is scheduled for removal in a "
                        "future release."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.14",
                    suggestion=(
                        f"Replace @{qualified} with the stacked form: "
                        f"{replacement}."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.14.html#deprecated"
                    ),
                    whatsnew_ref="3.14#deprecated",
                ))
        return findings
