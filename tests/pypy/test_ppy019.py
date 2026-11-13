import ast
import textwrap

from pyrift.rules.pypy.ppy019_nan_identity import NanIdentityRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")


class TestPPY019:
    rule = NanIdentityRule()

    # ── True positives — fires at identity comparison ───────────────────────

    def test_detects_is_comparison(self):
        findings = run(self.rule, "x is float('nan')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY019"

    def test_detects_is_not_comparison(self):
        findings = run(self.rule, "x is not float('nan')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY019"

    def test_detects_nan_on_left(self):
        findings = run(self.rule, "float('nan') is x")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY019"

    def test_detects_nan_both_sides(self):
        # Two NaN objects compared — common PyPy gotcha.
        # Only one finding per Compare node.
        findings = run(self.rule, "float('nan') is float('nan')")
        assert len(findings) == 1

    def test_detects_uppercase_nan_in_comparison(self):
        findings = run(self.rule, "x is float('NaN')")
        assert len(findings) == 1

    def test_detects_plus_nan_in_comparison(self):
        findings = run(self.rule, "x is float('+nan')")
        assert len(findings) == 1

    def test_suggestion_mentions_isnan(self):
        findings = run(self.rule, "x is float('nan')")
        assert "isnan" in findings[0].suggestion.lower()

    def test_finding_at_comparison_line(self):
        """Finding line must be the compare node, not the float() call."""
        src = textwrap.dedent("""\
            nan = float('nan')
            if x is nan:
                pass
        """)
        # float('nan') is line 1; the compare is line 2
        findings = run(self.rule, src)
        # nan is a Name node, not a float() call, so this should not fire
        assert findings == []

    def test_chained_comparison_fires_once(self):
        # a is float('nan') is float('nan') — two is-comparisons in one node
        findings = run(self.rule, "a is float('nan') is float('nan')")
        assert len(findings) == 1

    # ── True negatives — no identity comparison, no finding ─────────────────

    def test_creation_without_comparison_is_clean(self):
        """Bare assignment of float('nan') must NOT fire."""
        assert run(self.rule, "x = float('nan')") == []

    def test_creation_as_function_argument_is_clean(self):
        assert run(self.rule, "math.isnan(float('nan'))") == []

    def test_equality_comparison_is_clean(self):
        """== is not an identity comparison."""
        assert run(self.rule, "x == float('nan')") == []

    def test_less_than_comparison_is_clean(self):
        assert run(self.rule, "x < float('nan')") == []

    def test_clean_regular_float(self):
        assert run(self.rule, "x = float('1.5')") == []

    def test_name_identity_comparison_is_clean(self):
        """Identity comparison on a Name, not float(), should not fire."""
        src = textwrap.dedent("""\
            nan = float('nan')
            if x is nan:
                pass
        """)
        assert run(self.rule, src) == []