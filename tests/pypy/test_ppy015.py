import ast, textwrap
from pyrift.rules.pypy.ppy015_generator_gc import GeneratorGCRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY015:
    rule = GeneratorGCRule()

    def test_detects_yield_in_try(self):
        src = """
def gen():
    try:
        yield value
    finally:
        cleanup()
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY015"

    def test_detects_yield_in_with(self):
        src = """
def gen():
    with open('file') as f:
        yield f.read()
"""
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_clean_generator_no_try(self):
        src = """
def gen():
    for i in range(10):
        yield i
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_close(self):
        src = """
def gen():
    try:
        yield 1
    finally:
        pass
"""
        findings = run(self.rule, src)
        assert "close" in findings[0].suggestion.lower()