import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy020_kwargs_string_keys import KwargsStringKeysRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY020:
    rule = KwargsStringKeysRule()

    def test_detects_non_string_key_in_kwargs(self):
        findings = run(self.rule, "dict(**{1: 'value'})")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY020"
        assert findings[0].severity == Severity.ERROR

    def test_clean_string_keys(self):
        findings = run(self.rule, "dict(**{'key': 'value'})")
        assert len(findings) == 0

    def test_clean_regular_dict(self):
        findings = run(self.rule, "d = {1: 'value'}")
        assert len(findings) == 0

    def test_suggestion_mentions_string(self):
        findings = run(self.rule, "dict(**{1: 'x'})")
        assert "string" in findings[0].suggestion.lower()

    def test_unpack_of_non_dict_expression_is_clean(self):
        findings = run(self.rule, "f(**config)")
        assert findings == []

    def test_unpack_with_non_constant_key_is_clean(self):
        # A runtime-computed key cannot be proven non-string, so it is
        # left alone (conservative).
        findings = run(self.rule, "f(**{key: 1})")
        assert findings == []

    def test_unpack_with_none_key_is_clean(self):
        # {**d} uses None for the unpacked-key slot; must not crash or flag.
        findings = run(self.rule, "f(**{'a': 1}, **other)")
        assert findings == []

    def test_positional_star_args_are_clean(self):
        findings = run(self.rule, "f(*args)")
        assert findings == []

    def test_named_kwarg_with_dict_value_is_clean(self):
        findings = run(self.rule, "f(config={'a': 1, 2: 3})")
        assert findings == []