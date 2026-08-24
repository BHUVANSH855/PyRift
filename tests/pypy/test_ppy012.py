import ast, textwrap
from pyrift.rules.pypy.ppy012_subclassing_builtins import SubclassingBuiltinsRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY012:
    rule = SubclassingBuiltinsRule()

    def test_detects_dict_override(self):
        src = """
class MyDict(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY012"

    def test_detects_list_override(self):
        src = """
class MyList(list):
    def __setitem__(self, idx, val):
        super().__setitem__(idx, val)
"""
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_clean_subclass_no_override(self):
        src = """
class MyDict(dict):
    def my_method(self):
        pass
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_composition(self):
        src = """
class MyDict(dict):
    def __missing__(self, key):
        return None
"""
        findings = run(self.rule, src)
        assert "composition" in findings[0].suggestion.lower()