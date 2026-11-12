"""Tests for pyrift.versions — Ver, Interval, VersionFacts."""
from __future__ import annotations

import pytest

from pyrift.versions import Interval, Ver, VersionFacts


class TestVer:
    def test_ordering(self) -> None:
        assert Ver(3, 9) < Ver(3, 10)
        assert Ver(3, 10) > Ver(3, 9)
        assert Ver(3, 9) == Ver(3, 9)
        assert Ver(2, 7) < Ver(3, 0)

    def test_str(self) -> None:
        assert str(Ver(3, 10)) == "3.10"
        assert str(Ver(2, 7)) == "2.7"

    def test_parse_valid(self) -> None:
        assert Ver.parse("3.9") == Ver(3, 9)
        assert Ver.parse("3.10") == Ver(3, 10)
        assert Ver.parse("2.7") == Ver(2, 7)

    def test_parse_extra_components_accepted(self) -> None:
        # Only major.minor is used; patch component is ignored.
        assert Ver.parse("3.9.1") == Ver(3, 9)

    def test_parse_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            Ver.parse("3")
        with pytest.raises(ValueError):
            Ver.parse("three.nine")


class TestInterval:
    def test_contains_within_closed(self) -> None:
        iv = Interval(lo=Ver(3, 0), hi=Ver(3, 8))
        assert iv.contains(Ver(3, 0))
        assert iv.contains(Ver(3, 7))
        assert iv.contains(Ver(3, 8))

    def test_contains_outside_closed(self) -> None:
        iv = Interval(lo=Ver(3, 0), hi=Ver(3, 8))
        assert not iv.contains(Ver(2, 7))
        assert not iv.contains(Ver(3, 9))

    def test_open_upper_bound(self) -> None:
        iv = Interval(lo=Ver(3, 9), hi=None)
        assert iv.contains(Ver(3, 9))
        assert iv.contains(Ver(3, 12))
        assert not iv.contains(Ver(3, 8))

    def test_str_closed(self) -> None:
        assert str(Interval(lo=Ver(3, 0), hi=Ver(3, 8))) == "[3.0, 3.8]"

    def test_str_open(self) -> None:
        assert str(Interval(lo=Ver(3, 9), hi=None)) == "[3.9, ∞]"


class TestVersionFacts:
    def test_contains_delegates_to_interval(self) -> None:
        facts = VersionFacts(
            runtime="cpython",
            interval=Interval(lo=Ver(3, 0), hi=Ver(3, 8)),
        )
        assert facts.contains(Ver(3, 7))
        assert not facts.contains(Ver(3, 9))

    def test_str(self) -> None:
        facts = VersionFacts(
            runtime="cpython",
            interval=Interval(lo=Ver(3, 0), hi=Ver(3, 8)),
        )
        assert "cpython" in str(facts)
        assert "3.0" in str(facts)

    def test_runtime_stored(self) -> None:
        for rt in ("cpython", "pypy", "both"):
            facts = VersionFacts(
                runtime=rt,
                interval=Interval(lo=Ver(3, 0), hi=None),
            )
            assert facts.runtime == rt