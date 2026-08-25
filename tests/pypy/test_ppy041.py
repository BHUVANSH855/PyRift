import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy041_dict_merge_pypy import DictMergePypyRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestPPY041:
    rule = DictMergePypyRule()

    def test_detects_dict_merge_with_dict_variables(self):
        src = """
        a = {}
        b = {}
        d = a | b
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY041"
        assert findings[0].severity == Severity.INFO

    def test_detects_dict_merge_with_dict_literals(self):
        findings = run(self.rule, "{} | {}")

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY041"

    def test_detects_dict_constructor_operands(self):
        findings = run(
            self.rule,
            "d = dict() | dict()",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY041"

    def test_detects_annotated_dict_variables(self):
        src = """
        a: dict = {}
        b: dict = {}
        d = a | b
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY041"

    def test_clean_dict_unpack(self):
        findings = run(self.rule, "d = {**a, **b}")

        assert len(findings) == 0

    def test_clean_unknown_bitwise_or(self):
        findings = run(self.rule, "d = a | b")

        assert len(findings) == 0

    def test_clean_integer_bitwise_or(self):
        findings = run(self.rule, "d = 1 | 2")

        assert len(findings) == 0

    def test_clean_unknown_names(self):
        src = """
        left = get_value()
        right = get_value()
        result = left | right
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_suggestion_mentions_unpack(self):
        findings = run(self.rule, "{} | {}")

        assert len(findings) == 1
        assert "**" in findings[0].suggestion