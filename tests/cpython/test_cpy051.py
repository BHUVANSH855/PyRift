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

    def test_detects_mutated_module_level_list(self):
        findings = run(self.rule, "_cache = []\n_cache.append(1)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"
        assert findings[0].severity == Severity.WARNING

    def test_detects_mutated_module_level_dict(self):
        findings = run(self.rule, "_registry = {}\n_registry['x'] = 1")
        assert len(findings) == 1

    def test_detects_mutated_module_level_set(self):
        findings = run(self.rule, "_seen = {1, 2}\n_seen.add(3)")
        assert len(findings) == 1

    def test_plain_definition_is_not_enough(self):
        assert run(self.rule, "_cache = []") == []

    def test_set_constructor_is_not_flagged_without_mutation(self):
        assert run(self.rule, "_seen = set()") == []

    def test_immutable_module_level_value_is_clean(self):
        assert run(self.rule, "VERSION = '1.0'") == []

    def test_plain_reassignment_is_not_mutation(self):
        assert run(self.rule, "_cache = []\n_cache = [1]") == []

    def test_suggestion_mentions_lock(self):
        findings = run(self.rule, "_cache = []\n_cache.append(1)")
        assert "lock" in findings[0].suggestion.lower()
