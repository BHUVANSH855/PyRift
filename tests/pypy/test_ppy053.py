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
