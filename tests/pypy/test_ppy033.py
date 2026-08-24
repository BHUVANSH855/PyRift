import ast
import textwrap

from pyrift.rules.pypy.ppy033_del_ignored_exceptions import DelIgnoredExceptionsRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY033:
    rule = DelIgnoredExceptionsRule()

    def test_detects_del_with_calls(self):
        src = """
class MyClass:
    def __del__(self):
        self.cleanup()
        self.close()
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY033"

    def test_clean_empty_del(self):
        src = """
class MyClass:
    def __del__(self):
        pass
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_try_except(self):
        src = """
class MyClass:
    def __del__(self):
        self.close()
"""
        findings = run(self.rule, src)
        assert "try" in findings[0].suggestion.lower() or \
               "except" in findings[0].suggestion.lower()