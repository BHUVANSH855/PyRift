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
    """CPY023 was narrowed 2026-09-13 (review point 7): a bare
    `import multiprocessing` is no longer sufficient evidence that a
    program relies on fork semantics. The rule now requires an actual
    start-method-sensitive construct (Process/Pool/get_context without
    an explicit method)."""

    rule = MultiprocessingForkRule()

    def test_bare_import_does_not_trigger(self):
        # Importing the module proves nothing about reliance on the
        # default start method.
        findings = run(self.rule, "import multiprocessing")

        assert findings == []

    def test_detects_process_construction_without_target_platform(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            p = multiprocessing.Process(target=worker)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"
        assert findings[0].severity == Severity.WARNING

    def test_detects_pool_construction(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            with multiprocessing.Pool() as pool:
                pool.map(worker, items)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_does_not_flag_windows_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="windows"),
        )

        assert findings == []

    def test_does_not_flag_win32_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="win32"),
        )

        assert findings == []

    def test_does_not_flag_macos_target(self):
        # macOS has defaulted to 'spawn' since Python 3.8 -- it was
        # never 'fork' to begin with, so the 3.14 change is a no-op
        # there (review point 27).
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="macos"),
        )

        assert findings == []

    def test_does_not_flag_darwin_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="darwin"),
        )

        assert findings == []

    def test_flags_linux_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="linux"),
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_flags_posix_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
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
            p = multiprocessing.Process(target=worker)
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

    def test_flags_bare_get_context(self):
        # get_context() with no argument still defaults to the
        # platform default start method.
        findings = run(
            self.rule,
            """
            import multiprocessing
            ctx = multiprocessing.get_context()
            """,
        )

        assert len(findings) == 1

    def test_suggestion_mentions_set_start_method(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
        )

        assert (
            "set_start_method" in findings[0].suggestion.lower()
            or "fork" in findings[0].suggestion.lower()
        )
