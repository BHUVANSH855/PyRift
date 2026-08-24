import ast
import textwrap

from pyrift.rules.pypy.ppy028_readline_parse_bind import ReadlineParseBindRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY028:
    rule = ReadlineParseBindRule()

    def test_detects_parse_and_bind(self):
        findings = run(self.rule,
            "import readline\nreadline.parse_and_bind('tab: complete')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY028"

    def test_clean_other_readline_call(self):
        findings = run(self.rule,
            "import readline\nreadline.get_history_length()")
        assert len(findings) == 0

    def test_suggestion_mentions_pypy(self):
        findings = run(self.rule, "readline.parse_and_bind('tab: complete')")
        assert "pypy" in findings[0].suggestion.lower()