import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy050_purepatth_is_reserved import (
    PurePathIsReservedRule,
)


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY050:
    rule = PurePathIsReservedRule()

    def test_detects_purepath_is_reserved(self):
        findings = run(
            self.rule,
            """
            from pathlib import PurePath

            path = PurePath("CON")
            path.is_reserved()
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY050"
        assert findings[0].severity == Severity.WARNING

    def test_detects_pathlib_purepath_is_reserved(self):
        findings = run(
            self.rule,
            """
            import pathlib

            path = pathlib.PurePath("CON")
            path.is_reserved()
            """,
        )

        assert len(findings) == 1

    def test_detects_purepath_alias(self):
        findings = run(
            self.rule,
            """
            from pathlib import PurePath as PP

            path = PP("CON")
            path.is_reserved()
            """,
        )

        assert len(findings) == 1

    def test_detects_pathlib_alias(self):
        findings = run(
            self.rule,
            """
            import pathlib as pl

            path = pl.PurePath("CON")
            path.is_reserved()
            """,
        )

        assert len(findings) == 1

    def test_does_not_flag_unrelated_is_reserved_method(self):
        findings = run(
            self.rule,
            """
            validator.is_reserved()
            """,
        )

        assert len(findings) == 0

    def test_does_not_flag_unrelated_class_method(self):
        findings = run(
            self.rule,
            """
            class Validator:
                def is_reserved(self):
                    return False

            validator = Validator()
            validator.is_reserved()
            """,
        )

        assert len(findings) == 0

    def test_does_not_flag_unrelated_object_method(self):
        findings = run(
            self.rule,
            """
            custom_object.is_reserved()
            """,
        )

        assert len(findings) == 0

    def test_suggestion_mentions_os_path_isreserved(self):
        findings = run(
            self.rule,
            """
            from pathlib import PurePath

            path = PurePath("CON")
            path.is_reserved()
            """,
        )

        assert "os.path.isreserved" in findings[0].suggestion