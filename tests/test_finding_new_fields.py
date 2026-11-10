"""
Tests for new Finding fields added in v0.9.1:
  - whatsnew_ref / gh_issue cross-reference fields
  - whatsnew_url property
  - is_documented_change property
  - confidence_tier property
"""
from __future__ import annotations

from pyrift.finding import Confidence
from pyrift.finding import Finding
from pyrift.finding import IntentBasis


# ── helpers ──────────────────────────────────────────────────────────────────

def _finding(**kwargs) -> Finding:
    # Use a rule_id that doesn't exist in RULE_METADATA so __post_init__
    # won't overwrite caller-supplied confidence/intent_basis values.
    defaults = {"file": "x.py", "line": 1, "rule_id": "TST000"}
    defaults.update(kwargs)
    return Finding(**defaults)


# ── whatsnew_url ─────────────────────────────────────────────────────────────

class TestWhatsnewUrl:
    def test_empty_ref_returns_empty_string(self):
        f = _finding(whatsnew_ref="")
        assert f.whatsnew_url == ""

    def test_ref_with_anchor(self):
        f = _finding(whatsnew_ref="3.13#some-anchor")
        assert f.whatsnew_url == (
            "https://docs.python.org/3/whatsnew/3.13.html#some-anchor"
        )

    def test_ref_without_anchor(self):
        f = _finding(whatsnew_ref="3.12")
        assert f.whatsnew_url == (
            "https://docs.python.org/3/whatsnew/3.12.html"
        )

    def test_ref_in_to_dict(self):
        # Use a rule with a known whatsnew_ref in RULE_METADATA (CPY022).
        f = Finding(file="x.py", line=1, rule_id="CPY022")
        d = f.to_dict()
        # whatsnew_ref should be populated from metadata
        assert "whatsnew_ref" in d
        assert "whatsnew_url" in d
        # explicit override also round-trips correctly
        f2 = _finding(whatsnew_ref="3.11#new-feature")
        d2 = f2.to_dict()
        assert d2["whatsnew_ref"] == "3.11#new-feature"
        assert d2["whatsnew_url"] == (
            "https://docs.python.org/3/whatsnew/3.11.html#new-feature"
        )


# ── is_documented_change ─────────────────────────────────────────────────────

class TestIsDocumentedChange:
    def test_documented_intent_is_true(self):
        f = _finding(intent_basis=IntentBasis.DOCUMENTED)
        assert f.is_documented_change is True

    def test_deprecation_intent_is_true(self):
        f = _finding(intent_basis=IntentBasis.DEPRECATION)
        assert f.is_documented_change is True

    def test_observed_intent_is_false(self):
        f = _finding(intent_basis=IntentBasis.OBSERVED)
        assert f.is_documented_change is False

    def test_inferred_intent_is_false(self):
        f = _finding(intent_basis=IntentBasis.INFERRED)
        assert f.is_documented_change is False

    def test_implementation_defined_is_false(self):
        f = _finding(intent_basis=IntentBasis.IMPLEMENTATION_DEFINED)
        assert f.is_documented_change is False


# ── confidence_tier ───────────────────────────────────────────────────────────

class TestConfidenceTier:
    def test_high_tier(self):
        f = _finding(confidence=Confidence.HIGH)
        assert f.confidence_tier == "high"

    def test_medium_tier(self):
        f = _finding(confidence=Confidence.MEDIUM)
        assert f.confidence_tier == "medium"

    def test_low_tier(self):
        f = _finding(confidence=Confidence.LOW)
        assert f.confidence_tier == "low"

    def test_confidence_tier_in_to_dict(self):
        f = _finding(confidence=Confidence.HIGH)
        d = f.to_dict()
        assert d["confidence_tier"] == "high"


# ── gh_issue field ───────────────────────────────────────────────────────────

class TestGhIssue:
    def test_explicit_gh_issue(self):
        f = _finding(gh_issue="cpython/issues/12345")
        assert f.gh_issue == "cpython/issues/12345"

    def test_gh_issue_in_to_dict(self):
        f = _finding(gh_issue="bpo-123")
        d = f.to_dict()
        assert d["gh_issue"] == "bpo-123"

    def test_empty_by_default(self):
        f = _finding()
        assert f.gh_issue == ""


# ── config re-export module ───────────────────────────────────────────────────

class TestConfigModule:
    def test_config_module_importable(self):
        from pyrift.config import PyriftConfig, load_pyrift_config
        assert PyriftConfig is not None
        assert callable(load_pyrift_config)

    def test_pyrift_config_defaults(self):
        from pyrift.config import PyriftConfig
        cfg = PyriftConfig()
        assert cfg.select is None
        assert cfg.ignore is None
        assert cfg.format == ""
        assert cfg.fail_on_findings is False
        assert cfg.only_documented is False
