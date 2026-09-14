"""
Guards against the exact credibility failure identified in the 2026-09
architecture review, point 5: a rule must never be presented as
runtime-verified unless the harness actually has complete, passing
probe coverage for it.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _load_runtime_harness():
    spec = importlib.util.spec_from_file_location(
        "runtime_harness", ROOT / "benchmark" / "runtime_harness.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("runtime_harness", module)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class TestRuntimeVerificationHonesty:
    def test_fully_verified_rules_match_metadata_registry(self):
        """benchmark.runtime_harness.VERIFIED_RULES and
        pyrift.rule_metadata.FULLY_RUNTIME_VERIFIED_RULES must name the
        exact same set of rules. If they drift, either the harness
        checks a rule the metadata doesn't credit, or (worse) the
        metadata claims verification the harness never performs."""
        harness = _load_runtime_harness()
        from pyrift.rule_metadata import FULLY_RUNTIME_VERIFIED_RULES

        assert set(harness.VERIFIED_RULES) == FULLY_RUNTIME_VERIFIED_RULES

    def test_verified_rules_have_verifiers_for_every_required_version(self):
        """Every rule in VERIFIED_RULES must define a verifier
        (verify / verify_by_version) for every version it claims as
        affected or not-affected -- an incomplete entry here would
        silently degrade to a [FAIL] the harness catches at runtime,
        but we also check statically so CI fails fast without needing
        probe data."""
        harness = _load_runtime_harness()

        for rule_id, entry in harness.VERIFIED_RULES.items():
            affected = set(entry["versions_affected"])
            not_affected = set(entry.get("versions_not_affected", []))

            has_verify = entry.get("verify") is not None
            has_verify_by_version = entry.get("verify_by_version") is not None
            has_verify_not = entry.get("verify_not") is not None

            if affected:
                assert has_verify or has_verify_by_version, (
                    f"{rule_id} claims affected versions {affected} but "
                    "defines neither verify() nor verify_by_version()"
                )
            if not_affected:
                assert has_verify_not, (
                    f"{rule_id} claims non-affected versions {not_affected} "
                    "but defines no verify_not()"
                )

    def test_runtime_verification_state_never_claims_more_than_harness_checks(self):
        """Every rule NOT in FULLY_RUNTIME_VERIFIED_RULES must have
        runtime_verification == NOT_APPLICABLE in RULE_METADATA -- i.e.
        the metadata registry never silently upgrades a rule to
        VERIFIED/PARTIALLY_VERIFIED outside of what this harness
        actually checks."""
        from pyrift.finding import RuntimeVerificationState
        from pyrift.rule_metadata import (
            FULLY_RUNTIME_VERIFIED_RULES,
            RULE_METADATA,
        )

        for rule_id, entry in RULE_METADATA.items():
            state = entry.get("runtime_verification")
            if rule_id in FULLY_RUNTIME_VERIFIED_RULES:
                assert state == RuntimeVerificationState.VERIFIED
            else:
                assert state == RuntimeVerificationState.NOT_APPLICABLE, (
                    f"{rule_id} claims runtime_verification={state} but is "
                    "not in FULLY_RUNTIME_VERIFIED_RULES"
                )

    def test_main_exits_nonzero_when_no_probe_data_available(self, monkeypatch):
        """The old harness printed '[OK] Harness skipped' and returned 0
        when no probe files existed at all -- silently treating total
        absence of evidence as success. That must never happen again."""
        harness = _load_runtime_harness()

        monkeypatch.setattr(harness, "load_probe", lambda version: None)
        assert harness.main() == 1
