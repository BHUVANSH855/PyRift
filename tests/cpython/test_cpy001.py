import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy001_dict_ordering import DictOrderingRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY001:
    rule = DictOrderingRule()

    def test_detects_keys_vs_list(self):
        findings = run(self.rule, "d = {'a': 1}; assert d.keys() == ['a']")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY001"
        assert findings[0].severity == Severity.WARNING

    def test_detects_values_vs_list(self):
        findings = run(self.rule, "d = {'a': 1}; assert d.values() == [1]")
        assert len(findings) == 1

    def test_detects_items_vs_tuple(self):
        findings = run(self.rule, "assert d.items() == [('a', 1)]")
        assert len(findings) == 1

    def test_clean_vs_set_literal(self):
        findings = run(self.rule, "assert d.keys() == {'a', 'b'}")
        assert len(findings) == 0

    def test_clean_vs_set_call(self):
        findings = run(self.rule, "assert set(d.keys()) == {'a'}")
        assert len(findings) == 0

    def test_finding_has_suggestion(self):
        findings = run(self.rule, "d.keys() == ['a']")
        assert findings[0].suggestion != ""

    def test_suggestion_mentions_set(self):
        findings = run(self.rule, "d.keys() == ['a']")
        assert "set" in findings[0].suggestion.lower()