import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy002_exception_notes import ExceptionNotesRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY002:
    rule = ExceptionNotesRule()

    def test_detects_add_note(self):
        src = """
            try:
                pass
            except ValueError as e:
                e.add_note("extra context")
                raise
        """
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY002"
        assert findings[0].severity == Severity.ERROR

    def test_clean_code_no_finding(self):
        findings = run(self.rule, "e = ValueError('oops')")
        assert len(findings) == 0

    def test_docs_url_present(self):
        findings = run(self.rule, "e.add_note('note')")
        assert findings[0].docs_url != ""