import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy057_pickle_protocol import PickleProtocolRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: PickleProtocolRule, src: str) -> list:
    return rule.check(parse(src), "<test>")


class TestCPY057:
    rule = PickleProtocolRule()

    # --- pickle.dumps --- #

    def test_detects_dumps_no_protocol(self):
        findings = run(self.rule, "pickle.dumps(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY057"
        assert findings[0].severity == Severity.WARNING

    def test_detects_dumps_protocol_none_keyword(self):
        findings = run(self.rule, "pickle.dumps(obj, protocol=None)")
        assert len(findings) == 1

    def test_detects_dumps_protocol_none_positional(self):
        findings = run(self.rule, "pickle.dumps(obj, None)")
        assert len(findings) == 1

    def test_clean_dumps_protocol_4_keyword(self):
        findings = run(self.rule, "pickle.dumps(obj, protocol=4)")
        assert len(findings) == 0

    def test_clean_dumps_protocol_4_positional(self):
        findings = run(self.rule, "pickle.dumps(obj, 4)")
        assert len(findings) == 0

    def test_clean_dumps_protocol_5_keyword(self):
        findings = run(self.rule, "pickle.dumps(obj, protocol=5)")
        assert len(findings) == 0

    def test_clean_dumps_highest_protocol(self):
        findings = run(self.rule, "pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)")
        assert len(findings) == 0

    # --- pickle.dump --- #

    def test_detects_dump_no_protocol(self):
        findings = run(self.rule, "pickle.dump(obj, f)")
        assert len(findings) == 1

    def test_detects_dump_protocol_none_keyword(self):
        findings = run(self.rule, "pickle.dump(obj, f, protocol=None)")
        assert len(findings) == 1

    def test_detects_dump_protocol_none_positional(self):
        findings = run(self.rule, "pickle.dump(obj, f, None)")
        assert len(findings) == 1

    def test_clean_dump_protocol_4_keyword(self):
        findings = run(self.rule, "pickle.dump(obj, f, protocol=4)")
        assert len(findings) == 0

    def test_clean_dump_protocol_4_positional(self):
        findings = run(self.rule, "pickle.dump(obj, f, 4)")
        assert len(findings) == 0

    # --- pickle.Pickler --- #

    def test_detects_pickler_no_protocol(self):
        findings = run(self.rule, "pickle.Pickler(f)")
        assert len(findings) == 1

    def test_detects_pickler_protocol_none_positional(self):
        findings = run(self.rule, "pickle.Pickler(f, None)")
        assert len(findings) == 1

    def test_detects_pickler_protocol_none_keyword(self):
        findings = run(self.rule, "pickle.Pickler(f, protocol=None)")
        assert len(findings) == 1

    def test_clean_pickler_protocol_4_positional(self):
        findings = run(self.rule, "pickle.Pickler(f, 4)")
        assert len(findings) == 0

    def test_clean_pickler_protocol_4_keyword(self):
        findings = run(self.rule, "pickle.Pickler(f, protocol=4)")
        assert len(findings) == 0

    # --- pickle.loads (should never flag) --- #

    def test_clean_loads(self):
        findings = run(self.rule, "pickle.loads(data)")
        assert len(findings) == 0

    def test_clean_load(self):
        findings = run(self.rule, "pickle.load(f)")
        assert len(findings) == 0

    # --- suggestion quality --- #

    def test_suggestion_mentions_protocol(self):
        findings = run(self.rule, "pickle.dumps(obj)")
        assert "protocol" in findings[0].suggestion.lower()

    def test_description_mentions_none(self):
        findings = run(self.rule, "pickle.dumps(obj, None)")
        assert "None" in findings[0].description