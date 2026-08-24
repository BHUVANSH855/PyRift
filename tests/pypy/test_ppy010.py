import ast, textwrap
from pyrift.rules.pypy.ppy010_gc_collect import GcCollectRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY010:
    rule = GcCollectRule()

    def test_detects_gc_collect(self):
        findings = run(self.rule, "import gc\ngc.collect()")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY010"

    def test_clean_gc_get_referrers(self):
        findings = run(self.rule, "import gc\ngc.get_referrers(obj)")
        assert len(findings) == 0

    def test_suggestion_mentions_cleanup(self):
        findings = run(self.rule, "gc.collect()")
        assert "context manager" in findings[0].suggestion.lower() or \
               "close" in findings[0].suggestion.lower()