import ast
import textwrap

from pyrift.rules.pypy.ppy022_hash_randomisation import HashRandomisationRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: HashRandomisationRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY022:
    rule = HashRandomisationRule()

    def test_detects_pythonhashseed_environ_read(self):
        findings = run(
            self.rule,
            "import os\nseed = os.environ['PYTHONHASHSEED']",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY022"

    def test_does_not_flag_pythonhashseed_environ_write(self):
        findings = run(
            self.rule,
            "import os\nos.environ['PYTHONHASHSEED'] = '0'",
        )

        assert len(findings) == 0

    def test_detects_getenv(self):
        findings = run(
            self.rule,
            "import os\nseed = os.getenv('PYTHONHASHSEED')",
        )

        assert len(findings) == 1

    def test_detects_getenv_with_default(self):
        findings = run(
            self.rule,
            "import os\nseed = os.getenv('PYTHONHASHSEED', '0')",
        )

        assert len(findings) == 1

    def test_clean_other_env_var(self):
        findings = run(
            self.rule,
            "import os\npath = os.environ['PATH']",
        )

        assert len(findings) == 0

    def test_clean_other_getenv(self):
        findings = run(
            self.rule,
            "import os\npath = os.getenv('PATH')",
        )

        assert len(findings) == 0

    def test_does_not_flag_aliased_os(self):
        findings = run(
            self.rule,
            """
            import os as operating_system
            seed = operating_system.getenv("PYTHONHASHSEED")
            """,
        )

        assert len(findings) == 0

    def test_does_not_flag_arbitrary_mapping(self):
        findings = run(
            self.rule,
            """
            env = {}
            seed = env["PYTHONHASHSEED"]
            """,
        )

        assert len(findings) == 0

    def test_does_not_flag_variable_subscript(self):
        findings = run(
            self.rule,
            """
            import os
            name = "PYTHONHASHSEED"
            seed = os.environ[name]
            """,
        )

        assert len(findings) == 0

    def test_nested_read_is_detected(self):
        findings = run(
            self.rule,
            """
            import os
            print(os.environ["PYTHONHASHSEED"])
            """,
        )

        assert len(findings) == 1

    def test_suggestion_mentions_sorted(self):
        findings = run(
            self.rule,
            "os.environ['PYTHONHASHSEED']",
        )

        assert "sorted" in findings[0].suggestion.lower()