"""
pyrift.versions — typed version-range model.

Provides lightweight dataclasses for describing which interpreter
versions a compatibility finding applies to, replacing bare strings
like ``"3.0"`` / ``"3.8"`` with structured, comparable objects.

Usage::

    from pyrift.versions import Ver, Interval, VersionFacts

    facts = VersionFacts(
        runtime="cpython",
        interval=Interval(lo=Ver(3, 0), hi=Ver(3, 8)),
    )
    assert facts.contains(Ver(3, 7))
    assert not facts.contains(Ver(3, 9))
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


class Ver(NamedTuple):
    """A two-component interpreter version (major, minor).

    Examples::

        Ver(3, 9) < Ver(3, 10)   # True
        Ver(3, 9) == Ver(3, 9)   # True
    """

    major: int
    minor: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"

    @classmethod
    def parse(cls, text: str) -> Ver:
        """Parse a ``"major.minor"`` string into a :class:`Ver`.

        :param text: Version string such as ``"3.9"`` or ``"3.10"``.
        :raises ValueError: If *text* is not in ``major.minor`` form.
        """
        parts = text.split(".")
        if len(parts) < 2:
            raise ValueError(
                f"Cannot parse version {text!r}: expected 'major.minor'"
            )
        try:
            return cls(int(parts[0]), int(parts[1]))
        except ValueError as exc:
            raise ValueError(
                f"Cannot parse version {text!r}: non-integer component"
            ) from exc


@dataclass(frozen=True)
class Interval:
    """A closed version interval *[lo, hi]*.

    Both endpoints are inclusive.  Use ``hi=None`` to express an
    open upper bound (i.e. "from *lo* onwards").

    Examples::

        Interval(lo=Ver(3, 0), hi=Ver(3, 8)).contains(Ver(3, 7))  # True
        Interval(lo=Ver(3, 9), hi=None).contains(Ver(3, 12))      # True
    """

    lo: Ver
    hi: Ver | None = None

    def contains(self, ver: Ver) -> bool:
        """Return whether *ver* falls within this interval."""
        if ver < self.lo:
            return False
        return not (self.hi is not None and ver > self.hi)

    def __str__(self) -> str:
        hi_str = str(self.hi) if self.hi is not None else "∞"
        return f"[{self.lo}, {hi_str}]"


@dataclass(frozen=True)
class VersionFacts:
    """Version applicability facts for a single finding.

    Attributes:
        runtime:  ``"cpython"``, ``"pypy"``, or ``"both"``.
        interval: The closed version interval the finding applies to.
    """

    runtime: str
    interval: Interval

    def contains(self, ver: Ver) -> bool:
        """Return whether *ver* is within the affected interval."""
        return self.interval.contains(ver)

    def __str__(self) -> str:
        return f"VersionFacts(runtime={self.runtime!r}, interval={self.interval})"