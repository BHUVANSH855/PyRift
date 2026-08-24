import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy023_multiprocessing_fork import MultiprocessingForkRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY023:
    rule = MultiprocessingForkRule()

    def test_detects_multiprocessing_import(self):
        findings = run(self.rule, "import multiprocessing")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"
        assert findings[0].severity == Severity.WARNING

    def test_clean_other_import(self):
        findings = run(self.rule, "import threading")
        assert len(findings) == 0

    def test_suggestion_mentions_set_start_method(self):
        findings = run(self.rule, "import multiprocessing")
        assert "set_start_method" in findings[0].suggestion.lower() or \
               "fork" in findings[0].suggestion.lower()