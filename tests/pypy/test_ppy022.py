import ast, textwrap
from pyrift.rules.pypy.ppy022_hash_randomisation import HashRandomisationRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY022:
    rule = HashRandomisationRule()

    def test_detects_pythonhashseed_environ(self):
        findings = run(self.rule,
            "import os\nseed = os.environ['PYTHONHASHSEED']")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY022"

    def test_detects_getenv(self):
        findings = run(self.rule,
            "import os\nseed = os.getenv('PYTHONHASHSEED')")
        assert len(findings) == 1

    def test_clean_other_env_var(self):
        findings = run(self.rule,
            "import os\npath = os.environ['PATH']")
        assert len(findings) == 0

    def test_suggestion_mentions_sorted(self):
        findings = run(self.rule,
            "os.environ['PYTHONHASHSEED']")
        assert "sorted" in findings[0].suggestion.lower()