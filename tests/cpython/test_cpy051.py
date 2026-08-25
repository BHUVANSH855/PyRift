import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy051_free_threaded_global_state import (
    FreeThreadedGlobalStateRule,
)


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY051:
    rule = FreeThreadedGlobalStateRule()

    def test_detects_module_level_list(self):
        src = "_cache = []"
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"
        assert findings[0].severity == Severity.WARNING

    def test_detects_module_level_dict(self):
        src = "_registry = {}"
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_detects_module_level_set(self):
        src = "_seen = set()"
        findings = run(self.rule, src)
        assert len(findings) == 0  # set() call not a set literal

    def test_detects_module_level_set_literal(self):
        src = "_seen = {1, 2, 3}"
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_clean_module_level_immutable(self):
        src = "VERSION = '1.0'"
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_lock(self):
        src = "_cache = []"
        findings = run(self.rule, src)
        assert "lock" in findings[0].suggestion.lower()