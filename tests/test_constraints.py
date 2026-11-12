"""Tests for pyrift.analysis.constraints.eval_condition."""
from __future__ import annotations

import pytest
from pyrift.analysis.constraints import eval_condition
from pyrift.versions import Interval, Ver, VersionFacts


def _facts(runtime: str, lo: Ver, hi: Ver | None = None) -> VersionFacts:
    return VersionFacts(runtime=runtime, interval=Interval(lo=lo, hi=hi))


class TestLeafAtoms:
    def test_version_gte_satisfied(self) -> None:
        facts = _facts("cpython", lo=Ver(3, 9))
        assert eval_condition({"type": "version_gte", "ver": Ver(3, 9)}, facts)

    def test_version_gte_not_satisfied(self) -> None:
        facts = _facts("cpython", lo=Ver(3, 8))
        assert not eval_condition({"type": "version_gte", "ver": Ver(3, 9)}, facts)

    def test_version_lte_satisfied(self) -> None:
        facts = _facts("cpython", lo=Ver(3, 0), hi=Ver(3, 8))
        assert eval_condition({"type": "version_lte", "ver": Ver(3, 8)}, facts)

    def test_version_lte_open_upper_not_satisfied(self) -> None:
        # No hi bound means the range extends to current; lte can't be True.
        facts = _facts("cpython", lo=Ver(3, 9))
        assert not eval_condition({"type": "version_lte", "ver": Ver(3, 9)}, facts)

    def test_impl_exact_match(self) -> None:
        facts = _facts("cpython", lo=Ver(3, 9))
        assert eval_condition({"type": "impl", "runtime": "cpython"}, facts)

    def test_impl_no_match(self) -> None:
        facts = _facts("pypy", lo=Ver(3, 9))
        assert not eval_condition({"type": "impl", "runtime": "cpython"}, facts)

    def test_impl_both_matches_any(self) -> None:
        for rt in ("cpython", "pypy"):
            facts = _facts("both", lo=Ver(3, 9))
            assert eval_condition({"type": "impl", "runtime": rt}, facts)


class TestCompound:
    def test_not_inverts(self) -> None:
        facts = _facts("cpython", lo=Ver(3, 9))
        inner = {"type": "version_gte", "ver": Ver(3, 9)}
        assert not eval_condition({"type": "not", "operand": inner}, facts)
        assert eval_condition({"type": "not", "operand": {"type": "version_gte", "ver": Ver(3, 10)}}, facts)

    def test_and_all_true(self) -> None:
        facts = _facts("cpython", lo=Ver(3, 9))
        cond = {
            "type": "and",
            "operands": [
                {"type": "version_gte", "ver": Ver(3, 9)},
                {"type": "impl", "runtime": "cpython"},
            ],
        }
        assert eval_condition(cond, facts)

    def test_and_one_false(self) -> None:
        facts = _facts("pypy", lo=Ver(3, 9))
        cond = {
            "type": "and",
            "operands": [
                {"type": "version_gte", "ver": Ver(3, 9)},
                {"type": "impl", "runtime": "cpython"},
            ],
        }
        assert not eval_condition(cond, facts)

    def test_or_one_true(self) -> None:
        facts = _facts("pypy", lo=Ver(3, 9))
        cond = {
            "type": "or",
            "operands": [
                {"type": "impl", "runtime": "cpython"},
                {"type": "impl", "runtime": "pypy"},
            ],
        }
        assert eval_condition(cond, facts)

    def test_or_all_false(self) -> None:
        facts = _facts("pypy", lo=Ver(3, 8))
        cond = {
            "type": "or",
            "operands": [
                {"type": "impl", "runtime": "cpython"},
                {"type": "version_gte", "ver": Ver(3, 9)},
            ],
        }
        assert not eval_condition(cond, facts)

    def test_nested_not_and_or(self) -> None:
        facts = _facts("cpython", lo=Ver(3, 10))
        # (cpython AND >= 3.10) OR (pypy AND >= 3.9)
        cond = {
            "type": "or",
            "operands": [
                {
                    "type": "and",
                    "operands": [
                        {"type": "impl", "runtime": "cpython"},
                        {"type": "version_gte", "ver": Ver(3, 10)},
                    ],
                },
                {
                    "type": "and",
                    "operands": [
                        {"type": "impl", "runtime": "pypy"},
                        {"type": "version_gte", "ver": Ver(3, 9)},
                    ],
                },
            ],
        }
        assert eval_condition(cond, facts)


class TestUnknownType:
    def test_raises_value_error(self) -> None:
        facts = _facts("cpython", lo=Ver(3, 9))
        with pytest.raises(ValueError, match="Unknown condition type"):
            eval_condition({"type": "bogus"}, facts)