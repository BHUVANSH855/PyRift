import ast
import textwrap

from pyrift.rules.pypy.ppy032_dict_key_mutation import DictKeyMutationRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY032:
    rule = DictKeyMutationRule()

    def test_detects_set_as_dict_key(self):
        findings = run(self.rule, "d = {{1, 2}: 'value'}")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY032"

    def test_clean_frozenset_key(self):
        findings = run(self.rule, "d = {frozenset([1,2]): 'value'}")
        assert len(findings) == 0

    def test_suggestion_mentions_frozenset(self):
        findings = run(self.rule, "d = {{1}: 'v'}")
        if findings:
            assert "frozenset" in findings[0].suggestion.lower()