import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy068_typing_no_type_check_decorator import TypingNoTypeCheckDecoratorRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY068:
    rule = TypingNoTypeCheckDecoratorRule()

    def test_detects_import(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY068"
        assert findings[0].severity == Severity.WARNING

    def test_detects_attribute_access(self):
        findings = run(self.rule, "@typing.no_type_check_decorator\ndef f(): pass")
        assert len(findings) >= 1

    def test_clean_no_type_check(self):
        findings = run(self.rule, "from typing import no_type_check")
        assert len(findings) == 0

    def test_suggestion_mentions_no_type_check(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert "no_type_check" in findings[0].suggestion
