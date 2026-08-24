import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy041_dict_merge_operator import DictMergeOperatorRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY041:
    rule = DictMergeOperatorRule()

    def test_detects_dict_merge(self):
        findings = run(self.rule, "d = {'a': 1} | {'b': 2}")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY041"
        assert findings[0].severity == Severity.ERROR

    def test_detects_dict_update_operator(self):
        findings = run(self.rule, "d1 = {}\nd1 |= {'a': 1}")
        assert len(findings) == 1

    def test_clean_dict_unpack(self):
        findings = run(self.rule, "d = {**d1, **d2}")
        assert len(findings) == 0

    def test_suggestion_mentions_unpack(self):
        findings = run(self.rule, "d = {'a': 1} | {'b': 2}")
        assert "**" in findings[0].suggestion