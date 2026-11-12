"""
pyrift.analysis.constraints — guard-condition evaluator.

Evaluates compound boolean version/implementation guard conditions of
the form produced by the CPython/PyPy guard engine, returning whether a
given :class:`~pyrift.versions.VersionFacts` satisfies the guard.

Supported condition shapes::

    # Leaf atoms
    {"type": "version_gte", "ver": Ver(3, 9)}
    {"type": "version_lte", "ver": Ver(3, 8)}
    {"type": "impl",        "runtime": "cpython"}

    # Compound
    {"type": "not",  "operand": <condition>}
    {"type": "and",  "operands": [<condition>, ...]}
    {"type": "or",   "operands": [<condition>, ...]}

Usage::

    from pyrift.analysis.constraints import eval_condition
    from pyrift.versions import Ver, VersionFacts, Interval

    facts = VersionFacts(runtime="cpython",
                         interval=Interval(lo=Ver(3, 9), hi=Ver(3, 9)))
    cond  = {"type": "version_gte", "ver": Ver(3, 9)}
    assert eval_condition(cond, facts) is True
"""
from __future__ import annotations

from typing import Any

from pyrift.versions import Ver, VersionFacts

# Type alias for a condition dict (recursive structure).
Condition = dict[str, Any]


def eval_condition(condition: Condition, facts: VersionFacts) -> bool:
    """Evaluate *condition* against *facts*.

    :param condition: A condition mapping with a ``"type"`` key.
    :param facts: Runtime/version facts describing the execution context.
    :returns: ``True`` if *facts* satisfy *condition*, ``False`` otherwise.
    :raises ValueError: If the condition type is unknown.
    """
    ctype = condition.get("type")

    if ctype == "version_gte":
        threshold: Ver = condition["ver"]
        return facts.interval.lo >= threshold

    if ctype == "version_lte":
        threshold = condition["ver"]
        return facts.interval.hi is not None and facts.interval.hi <= threshold

    if ctype == "impl":
        required_runtime: str = condition["runtime"]
        return facts.runtime in (required_runtime, "both")

    if ctype == "not":
        return not eval_condition(condition["operand"], facts)

    if ctype == "and":
        return all(eval_condition(op, facts) for op in condition["operands"])

    if ctype == "or":
        return any(eval_condition(op, facts) for op in condition["operands"])

    raise ValueError(f"Unknown condition type: {ctype!r}")