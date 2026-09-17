import ast
import textwrap

from pyrift.rules.pypy.ppy025_set_ordering import SetOrderingRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY025:
    rule = SetOrderingRule()

    def test_detects_list_of_set_literal(self):
        findings = run(self.rule, "x = list({'a', 'b', 'c'})")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY025"

    def test_clean_list_of_list(self):
        findings = run(self.rule, "x = list(['a', 'b', 'c'])")
        assert len(findings) == 0

    def test_suggestion_mentions_sorted(self):
        findings = run(self.rule, "list({'a', 'b'})")
        assert "sorted" in findings[0].suggestion.lower()

class TestPPY025Framing:
    """2026-09 audit item #19: the finding should frame this as "your
    code depends on undefined set order" (a portability principle),
    not simply "PyPy differs from CPython" -- and the underlying claim
    (PyPy's own docs: "Dictionaries and sets are ordered on PyPy")
    should stay accurate."""

    rule = SetOrderingRule()

    def test_description_leads_with_portability_not_just_difference(self):
        findings = run(self.rule, "x = list({'a', 'b', 'c'})")
        description = findings[0].description.lower()
        assert "not part of the python language" in description or "not guaranteed" in description

    def test_description_still_states_accurate_facts(self):
        """The reframing shouldn't drop the underlying factual claim --
        it should still be there, just not leading."""
        findings = run(self.rule, "x = list({'a', 'b', 'c'})")
        description = findings[0].description.lower()
        assert "unordered" in description
        assert "insertion order" in description

    def test_for_loop_over_set_literal_also_reframed(self):
        findings = run(self.rule, "for x in {1, 2, 3}:\n    pass")
        description = findings[0].description.lower()
        assert "not part of the python language" in description or "not guaranteed" in description
