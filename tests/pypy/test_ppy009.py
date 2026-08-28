import ast
import textwrap

from pyrift.rules.pypy.ppy009_id_stability import IdStabilityRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: IdStabilityRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY009:
    rule = IdStabilityRule()

    def test_detects_id_comparison(self):
        findings = run(
            self.rule,
            "if id(x) == id(y): pass",
        )

        assert len(findings) == 2
        assert all(
            finding.rule_id == "PPY009"
            for finding in findings
        )

    def test_detects_returned_id(self):
        findings = run(
            self.rule,
            "def get_id(x): return id(x)",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY009"

    def test_detects_stored_id(self):
        findings = run(
            self.rule,
            "cached_id = id(obj)",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY009"

    def test_detects_stored_id_in_attribute(self):
        findings = run(
            self.rule,
            "self.cached_id = id(obj)",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY009"

    def test_detects_id_stored_in_list(self):
        findings = run(
            self.rule,
            "ids = [id(obj)]",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY009"

    def test_detects_id_stored_in_dict_value(self):
        findings = run(
            self.rule,
            "ids = {'object': id(obj)}",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY009"

    def test_detects_id_returned_inside_container(self):
        findings = run(
            self.rule,
            "def get_ids(x): return [id(x)]",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY009"

    def test_clean_id_as_dict_key(self):
        findings = run(
            self.rule,
            "parent_map[id(child)] = parent",
        )

        assert findings == []

    def test_clean_id_as_dict_key_in_expression(self):
        findings = run(
            self.rule,
            "value = mapping[id(child)]",
        )

        assert findings == []

    def test_clean_id_local_dedup(self):
        findings = run(
            self.rule,
            "node_id = id(n)",
        )

        assert findings == []

    def test_clean_id_child_dedup(self):
        findings = run(
            self.rule,
            "child_id = id(child)",
        )

        assert findings == []

    def test_clean_id_in_set(self):
        findings = run(
            self.rule,
            "seen = {id(x) for x in items}",
        )

        assert findings == []

    def test_clean_id_in_set_literal(self):
        findings = run(
            self.rule,
            "seen = {id(x), id(y)}",
        )

        assert findings == []

    def test_clean_id_in_set_call(self):
        findings = run(
            self.rule,
            "seen = set([id(x), id(y)])",
        )

        assert findings == []

    def test_clean_id_in_frozenset_call(self):
        findings = run(
            self.rule,
            "seen = frozenset((id(x), id(y)))",
        )

        assert findings == []

    def test_clean_id_tuple_dedup(self):
        findings = run(
            self.rule,
            "key = (id(n), mod)",
        )

        assert findings == []

    def test_does_not_flag_transient_function_argument(self):
        findings = run(
            self.rule,
            "print(id(obj))",
        )

        assert findings == []

    def test_does_not_flag_transient_expression(self):
        findings = run(
            self.rule,
            "id(obj)",
        )

        assert findings == []

    def test_suggestion_mentions_is(self):
        findings = run(
            self.rule,
            "if id(x) == id(y): pass",
        )

        assert "is" in findings[0].suggestion.lower()

    def test_finding_has_high_confidence(self):
        findings = run(
            self.rule,
            "cached_id = id(obj)",
        )

        assert findings[0].confidence.value == "high"