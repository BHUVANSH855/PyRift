import ast
import textwrap

from pyrift.rules.pypy.ppy009_id_stability import IdStabilityRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")


class TestPPY009:
    rule = IdStabilityRule()

    def test_detects_id_comparison(self):
        findings = run(self.rule, "if id(x) == id(y): pass")
        assert len(findings) >= 1
        assert findings[0].rule_id == "PPY009"

    def test_clean_id_as_dict_key(self):
        # Legitimate: parent_map[id(child)] = parent
        findings = run(self.rule, "parent_map[id(child)] = parent")
        assert len(findings) == 0

    def test_clean_id_local_variable(self):
        # Legitimate: local dedup variable
        findings = run(self.rule, "node_id = id(n)")
        assert len(findings) == 0

    def test_clean_id_in_set(self):
        findings = run(self.rule, "seen = {id(x) for x in items}")
        assert len(findings) == 0

    def test_clean_id_tuple_dedup(self):
        findings = run(self.rule, "key = (id(n), mod)")
        assert len(findings) == 0

    def test_suggestion_mentions_is(self):
        findings = run(self.rule, "if id(x) == id(y): pass")
        assert "is" in findings[0].suggestion.lower()