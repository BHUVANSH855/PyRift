import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
    MultiprocessingForkRule,
)
from pyrift.targets import TargetConfig


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src, target_config=None):
    return rule.check(
        parse(src),
        "<test>",
        target_config,
    )


class TestCPY023:
    rule = MultiprocessingForkRule()

    def test_detects_multiprocessing_import_without_target_platform(self):
        findings = run(self.rule, "import multiprocessing")

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"
        assert findings[0].severity == Severity.WARNING

    def test_does_not_flag_windows_target(self):
        findings = run(
            self.rule,
            "import multiprocessing",
            TargetConfig(platform="windows"),
        )

        assert findings == []

    def test_does_not_flag_win32_target(self):
        findings = run(
            self.rule,
            "import multiprocessing",
            TargetConfig(platform="win32"),
        )

        assert findings == []

    def test_flags_linux_target(self):
        findings = run(
            self.rule,
            "import multiprocessing",
            TargetConfig(platform="linux"),
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_flags_posix_target(self):
        findings = run(
            self.rule,
            "import multiprocessing",
            TargetConfig(platform="posix"),
        )

        assert len(findings) == 1

    def test_clean_other_import(self):
        findings = run(self.rule, "import threading")

        assert len(findings) == 0

    def test_does_not_flag_explicit_start_method(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            multiprocessing.set_start_method('fork')
            """,
        )

        assert findings == []

    def test_does_not_flag_explicit_get_context(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            ctx = multiprocessing.get_context('fork')
            """,
        )

        assert findings == []

    def test_suggestion_mentions_set_start_method(self):
        findings = run(self.rule, "import multiprocessing")

        assert (
            "set_start_method" in findings[0].suggestion.lower()
            or "fork" in findings[0].suggestion.lower()
        )
