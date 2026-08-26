"""
Tests for rule-inventory consistency across the project.

Every production rule must be represented consistently in:
- scanner registration
- authoritative metadata
- golden benchmark cases
- expected quality contracts
- rule documentation
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pyrift.rule_metadata import RULE_METADATA
from pyrift.scanner import ALL_RULES

ROOT = Path(__file__).resolve().parents[1]


def _expected_contract_ids() -> set[str]:
    path = ROOT / "benchmark" / "expected.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return set(data["rules"])


def _golden_rule_ids() -> set[str]:
    path = ROOT / "benchmark" / "run_benchmark.py"
    text = path.read_text(encoding="utf-8")
    return set(
        re.findall(r'^    "((?:CPY|PPY)\d+)"\s*:\s*\[', text, re.MULTILINE)
    )


def _documented_rule_ids() -> set[str]:
    path = ROOT / "docs" / "rules.md"
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"\b(?:CPY|PPY)\d{3}\b", text))


def _test_rule_ids() -> set[str]:
    rule_ids: set[str] = set()

    for path in (ROOT / "tests").rglob("test_*.py"):
        match = re.fullmatch(
            r"test_(?:rule_)?(cpy|ppy)(\d+)\.py",
            path.name,
            re.IGNORECASE,
        )
        if match:
            rule_ids.add(
                f"{match.group(1).upper()}{int(match.group(2)):03d}"
            )

    return rule_ids


def test_rule_inventory_matches_metadata() -> None:
    registered = {rule.rule_id for rule in ALL_RULES}
    metadata = set(RULE_METADATA)

    assert registered == metadata


def test_rule_inventory_matches_quality_contracts() -> None:
    registered = {rule.rule_id for rule in ALL_RULES}
    contracts = _expected_contract_ids()

    assert registered == contracts


def test_rule_inventory_matches_golden_benchmark() -> None:
    registered = {rule.rule_id for rule in ALL_RULES}
    golden = _golden_rule_ids()

    assert registered == golden


def test_rule_inventory_is_documented() -> None:
    registered = {rule.rule_id for rule in ALL_RULES}
    documented = _documented_rule_ids()

    missing = registered - documented
    assert not missing, f"Undocumented rules: {sorted(missing)}"


def test_rule_inventory_has_dedicated_tests() -> None:
    registered = {rule.rule_id for rule in ALL_RULES}
    tested = _test_rule_ids()

    missing = registered - tested
    extra = tested - registered

    assert not missing, f"Rules without dedicated tests: {sorted(missing)}"
    assert not extra, f"Tests without registered rules: {sorted(extra)}"