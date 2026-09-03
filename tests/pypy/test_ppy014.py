import ast
import textwrap

from pyrift.rules.pypy.ppy014_string_concat import StringConcatLoopRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestPPY014:
    rule = StringConcatLoopRule()

    def test_detects_string_concat_in_for_loop(self):
        src = """
        result = ""
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY014"

    def test_detects_string_concat_in_while_loop(self):
        src = """
        s = ""
        while condition:
            s += chunk
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY014"

    def test_detects_annotated_string(self):
        src = """
        result: str = ""
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY014"

    def test_detects_f_string_initialization(self):
        src = """
        result = f"{prefix}"
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY014"

    def test_clean_join_pattern(self):
        src = """
        parts = []
        for item in items:
            parts.append(item)
        result = ''.join(parts)
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_integer_addition(self):
        src = """
        result = 0
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_float_addition(self):
        src = """
        result = 0.0
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_list_addition(self):
        src = """
        result = []
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_unknown_variable(self):
        src = """
        result = get_value()
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_unknown_augmented_assignment(self):
        src = """
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_suggestion_mentions_join(self):
        src = """
        result = ""
        for item in items:
            result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert "join" in findings[0].suggestion.lower()

    def test_nested_loop_reports_each_string_concat_once(self):
        src = """
        result = ""
        for outer in items:
            result += outer
            for inner in outer:
                result += inner
        """

        findings = run(self.rule, src)

        assert len(findings) == 2
        assert all(
            finding.rule_id == "PPY014"
            for finding in findings
        )

    def test_does_not_duplicate_nested_loop_concat(self):
        src = """
        result = ""
        for outer in items:
            for inner in outer:
                result += inner
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY014"

    def test_nested_loop_concat_is_reported_by_inner_loop_only(self):
        src = """
        result = ""
        for outer in items:
            for inner in outer:
                result += inner
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].line == 5

    def test_string_name_does_not_leak_between_functions(self):
        src = """
        def first():
            result = ""

        def second():
            for item in items:
                result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_same_name_in_different_functions_is_independent(self):
        src = """
        def first():
            result = ""
            for item in items:
                result += item

        def second():
            result = 0
            for item in items:
                result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].line == 5

    def test_nested_function_does_not_inherit_outer_string_name(self):
        src = """
        result = ""

        def inner():
            for item in items:
                result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_nested_function_can_have_its_own_string_name(self):
        src = """
        result = ""

        def inner():
            result = ""
            for item in items:
                result += item
        """

        findings = run(self.rule, src)

        assert len(findings) == 1