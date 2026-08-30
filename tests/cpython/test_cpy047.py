import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy047_bytesstring_removed import ByteStringRemovedRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY047:
    rule = ByteStringRemovedRule()

    def test_detects_import_bytestring(self):
        findings = run(self.rule,
            "from collections.abc import ByteString")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY047"
        assert findings[0].severity == Severity.WARNING  # deprecated, not yet removed

    def test_detects_attribute_access(self):
        findings = run(self.rule,
            "import collections.abc\nx = collections.abc.ByteString")
        assert len(findings) >= 1

    def test_clean_other_collections_import(self):
        findings = run(self.rule,
            "from collections.abc import Sequence")
        assert len(findings) == 0

    def test_suggestion_mentions_union(self):
        findings = run(self.rule,
            "from collections.abc import ByteString")
        assert "Union" in findings[0].suggestion or \
               "union" in findings[0].suggestion.lower()