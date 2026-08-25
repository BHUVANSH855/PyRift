import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy049_compression_zstd import CompressionZstdRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY049:
    rule = CompressionZstdRule()

    def test_detects_import_compression_zstd(self):
        findings = run(self.rule, "import compression.zstd")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY049"
        assert findings[0].severity == Severity.ERROR

    def test_detects_from_import(self):
        findings = run(self.rule,
            "from compression.zstd import ZstdCompressor")
        assert len(findings) == 1

    def test_clean_other_compression(self):
        findings = run(self.rule, "import zlib")
        assert len(findings) == 0

    def test_suggestion_mentions_zstandard(self):
        findings = run(self.rule, "import compression.zstd")
        assert "zstandard" in findings[0].suggestion.lower()