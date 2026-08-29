import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy041_dict_merge_operator import DictMergeOperatorRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")


class TestCPY041:
    rule = DictMergeOperatorRule()

    def test_detects_dict_literal_merge(self):
        findings = run(self.rule, "d = {'a': 1} | {'b': 2}")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY041"
        assert findings[0].severity == Severity.ERROR

    def test_detects_dict_literal_left(self):
        findings = run(self.rule, "d = {} | other")
        assert len(findings) == 1

    def test_detects_dict_literal_right(self):
        findings = run(self.rule, "d = other | {}")
        assert len(findings) == 1

    def test_detects_augmented_assign_dict_name(self):
        findings = run(self.rule, "d |= {'key': 'val'}")
        assert len(findings) == 1

    def test_detects_augmented_assign_dict_like_names(self):
        for name in ("data", "config", "options", "settings", "kwargs",
                      "params", "cache", "result", "output", "info"):
            code = f"{name} |= {{}}"
            findings = run(self.rule, code)
            assert len(findings) == 1, f"Expected flag for {name}"

    def test_clean_augmented_assign_int_like(self):
        code = "flags |= FLAG_A"
        assert len(run(self.rule, code)) == 0

    def test_clean_augmented_assign_set_like(self):
        code = "set1 |= set2"
        assert len(run(self.rule, code)) == 0

    def test_clean_augmented_assign_non_dict_names(self):
        for name in ("x", "y", "count", "total", "value", "flag", "mask",
                      "size", "length", "index", "level", "mode", "type",
                      "kind", "code", "status", "error", "i", "j", "n"):
            code = f"{name} |= other"
            assert len(run(self.rule, code)) == 0, f"Should not flag {name}"

    def test_clean_bare_name_bitor(self):
        findings = run(self.rule, "x = a | b")
        assert len(findings) == 0

    def test_clean_bitflags_pattern(self):
        findings = run(self.rule, "flags = READ | WRITE | EXEC")
        assert len(findings) == 0

    def test_clean_set_union(self):
        findings = run(self.rule, "result = set_a | set_b")
        assert len(findings) == 0

    def test_suggestion_mentions_unpack(self):
        findings = run(self.rule, "d = {'a': 1} | {'b': 2}")
        assert "**" in findings[0].suggestion
