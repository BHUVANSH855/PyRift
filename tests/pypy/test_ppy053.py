import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy053_lru_cache_thread_safety import LruCacheThreadSafetyRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY053:
    rule = LruCacheThreadSafetyRule()

    def test_detects_lru_cache(self):
        findings = run(self.rule, "@functools.lru_cache\ndef f(): pass")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY053"
        assert findings[0].severity == Severity.INFO

    def test_detects_lru_cache_with_maxsize(self):
        findings = run(self.rule, "@functools.lru_cache(maxsize=128)\ndef f(): pass")
        assert len(findings) == 1

    def test_detects_bare_lru_cache(self):
        findings = run(self.rule, "@lru_cache\ndef f(): pass")
        assert len(findings) == 1

    def test_clean_other_decorator(self):
        findings = run(self.rule, "@functools.wraps\ndef f(): pass")
        assert len(findings) == 0

    def test_suggestion_mentions_threading(self):
        findings = run(self.rule, "@functools.lru_cache\ndef f(): pass")
        assert "thread" in findings[0].suggestion.lower() or "cache" in findings[0].suggestion.lower()


class TestPPY053EvidenceStatus:
    """2026-09 audit item #15: PPY053's thread-safety/locking-strategy
    claim rests on general/observed evidence rather than a specific,
    citable PyPy documentation section -- it must not present with the
    same confidence as a Tier A rule, and should be marked experimental
    until stronger evidence exists."""

    rule = LruCacheThreadSafetyRule()

    def test_marked_low_confidence_tier_c(self):
        from pyrift.finding import Confidence, RuleTier
        from pyrift.rule_metadata import RULE_METADATA

        metadata = RULE_METADATA["PPY053"]
        assert metadata["confidence"] == Confidence.LOW
        assert metadata["rule_tier"] == RuleTier.TIER_C

    def test_marked_experimental_status(self):
        from pyrift.rule_metadata import RULE_METADATA

        assert RULE_METADATA["PPY053"]["status"] == "experimental"

    def test_finding_severity_stays_info_not_warning(self):
        """An experimental, Tier C, low-confidence rule should not
        present at WARNING/ERROR severity, which would visually equate
        it with well-evidenced rules in CI output."""
        findings = run(self.rule, "@functools.lru_cache\ndef f(): pass")
        assert findings[0].severity == Severity.INFO

    def test_rule_status_flows_through_to_finding(self):
        findings = run(self.rule, "@functools.lru_cache\ndef f(): pass")
        assert findings[0].rule_status == "experimental"
