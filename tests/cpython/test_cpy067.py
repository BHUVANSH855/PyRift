import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy067_typing_namedtuple_keyword import TypingNamedTupleKeywordRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY067:
    rule = TypingNamedTupleKeywordRule()

    def test_detects_keyword_syntax(self):
        code = "from typing import NamedTuple\nPoint = NamedTuple('Point', x=int, y=int)"
        findings = run(self.rule, code)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY067"
        assert findings[0].severity == Severity.WARNING

    def test_detects_typing_keyword_syntax(self):
        code = "import typing\nPoint = typing.NamedTuple('Point', x=int, y=int)"
        findings = run(self.rule, code)
        assert len(findings) == 1

    def test_clean_class_syntax(self):
        code = "from typing import NamedTuple\nclass Point(NamedTuple):\n    x: int\n    y: int"
        findings = run(self.rule, code)
        assert len(findings) == 0

    def test_clean_dict_syntax(self):
        code = "from typing import NamedTuple\nPoint = NamedTuple('Point', {'x': int, 'y': int})"
        # This is the dict form - should also be detected
        findings = run(self.rule, code)
        assert len(findings) == 1

    def test_suggestion_mentions_class(self):
        code = "from typing import NamedTuple\nPoint = NamedTuple('Point', x=int)"
        findings = run(self.rule, code)
        assert "class" in findings[0].suggestion.lower()
