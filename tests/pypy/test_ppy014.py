import ast
import textwrap

from pyrift.rules.pypy.ppy014_string_concat import StringConcatLoopRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY014:
    rule = StringConcatLoopRule()

    def test_detects_concat_in_for_loop(self):
        src = """
for item in items:
    result += item
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY014"

    def test_detects_concat_in_while_loop(self):
        src = """
while condition:
    s += chunk
"""
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_clean_join_pattern(self):
        src = """
parts = []
for item in items:
    parts.append(item)
result = ''.join(parts)
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_join(self):
        src = "for x in xs:\n    s += x"
        findings = run(self.rule, src)
        assert "join" in findings[0].suggestion.lower()