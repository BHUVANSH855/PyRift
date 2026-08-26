import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy050_purepath_is_reserved import PurePathIsReservedRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: PurePathIsReservedRule, src: str) -> list:
    return rule.check(parse(src), "<test>")


class TestCPY050:
    rule = PurePathIsReservedRule()

    def test_detects_purepath_is_reserved(self):
        src = """
from pathlib import PurePath
p = PurePath('CON')
p.is_reserved()
"""
        findings = run(self.rule, src)
        assert len(findings) >= 1
        assert findings[0].rule_id == "CPY050"
        assert findings[0].severity == Severity.WARNING

    def test_no_finding_without_pathlib_import(self):
        # Without pathlib import context rule correctly returns no findings
        findings = run(self.rule, "p.is_reserved()")
        assert len(findings) == 0

    def test_detects_via_assignment(self):
        src = """
from pathlib import PurePath
p = PurePath('NUL')
result = p.is_reserved()
"""
        findings = run(self.rule, src)
        assert len(findings) >= 1

    def test_clean_other_is_method(self):
        src = """
from pathlib import PurePath
p = PurePath('/tmp')
p.is_absolute()
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_clean_no_pathlib_import(self):
        # Without pathlib import context rule should not flag
        findings = run(self.rule, "p.is_reserved()")
        assert len(findings) == 0

    def test_suggestion_mentions_os_path(self):
        src = """
from pathlib import PurePath
p = PurePath('CON')
p.is_reserved()
"""
        findings = run(self.rule, src)
        assert len(findings) >= 1
        assert "os.path.isreserved" in findings[0].suggestion

    def test_title_mentions_version(self):
        src = """
from pathlib import PurePath
p = PurePath('CON')
p.is_reserved()
"""
        findings = run(self.rule, src)
        assert len(findings) >= 1
        assert "3.13" in findings[0].title or "3.15" in findings[0].title

    def test_description_mentions_deprecation(self):
        src = """
from pathlib import PurePath
p = PurePath('CON')
p.is_reserved()
"""
        findings = run(self.rule, src)
        assert len(findings) >= 1
        desc = findings[0].description.lower()
        assert "deprecated" in desc or "removed" in desc