import ast, textwrap
from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY004:
    rule = WeakrefProxyRule()

    def test_detects_weakref_proxy(self):
        findings = run(self.rule, "import weakref\np = weakref.proxy(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY004"

    def test_clean_weakref_ref(self):
        findings = run(self.rule, "import weakref\nr = weakref.ref(obj)")
        assert len(findings) == 0

    def test_suggestion_mentions_ref(self):
        findings = run(self.rule, "weakref.proxy(obj)")
        assert "ref()" in findings[0].suggestion