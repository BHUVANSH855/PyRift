import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy057_pickle_protocol import PickleProtocolRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY057:
    rule = PickleProtocolRule()

    def test_detects_pickle_dumps_no_protocol(self):
        findings = run(self.rule, "import pickle\npickle.dumps(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY057"
        assert findings[0].severity == Severity.WARNING

    def test_detects_pickle_dump_no_protocol(self):
        findings = run(self.rule,
            "import pickle\npickle.dump(obj, f)")
        assert len(findings) == 1

    def test_clean_pickle_dumps_with_protocol(self):
        findings = run(self.rule,
            "import pickle\npickle.dumps(obj, protocol=4)")
        assert len(findings) == 0

    def test_clean_pickle_dumps_positional_protocol(self):
        findings = run(self.rule,
            "import pickle\npickle.dumps(obj, 4)")
        assert len(findings) == 0

    def test_suggestion_mentions_protocol(self):
        findings = run(self.rule, "pickle.dumps(obj)")
        assert "protocol" in findings[0].suggestion.lower()