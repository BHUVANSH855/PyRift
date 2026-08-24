import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy041_dict_merge_pypy import DictMergePypyRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY041:
    rule = DictMergePypyRule()

    def test_detects_dict_merge_on_pypy(self):
        findings = run(self.rule, "d = a | b")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY041"
        assert findings[0].severity == Severity.INFO

    def test_clean_dict_unpack(self):
        findings = run(self.rule, "d = {**a, **b}")
        assert len(findings) == 0

    def test_suggestion_mentions_unpack(self):
        findings = run(self.rule, "d = a | b")
        assert "**" in findings[0].suggestion