"""
Platform-sensitivity tests.

These verify that OS-sensitive rules behave sanely regardless of the
host operating system. They are run on Linux, macOS, and Windows in CI.

The rules themselves are pure AST analysis (deterministic on the source),
so the assertions here must hold on every platform. Any failure signals
that a rule accidentally depends on host-OS behaviour instead of the
target-platform metadata it declares.
"""
from __future__ import annotations

import ast
import os
import textwrap

import pytest

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
from pyrift.rules.cpython.cpy050_purepath_is_reserved import (
    PurePathIsReservedRule,
)
from pyrift.rules.pypy.ppy039_os_fork import OsForkRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


class TestPlatformSensitiveRules:
    def test_purepath_is_reserved_flags_on_all_platforms(self):
        """CPY050 is a deprecation flag that is valid on every OS."""
        rule = PurePathIsReservedRule()
        findings = rule.check(
            parse(
                """
                from pathlib import PurePath
                p = PurePath("CON")
                p.is_reserved()
                """
            ),
            "<test>",
        )
        assert findings
        assert findings[0].rule_id == "CPY050"
        assert findings[0].severity == Severity.WARNING

    def test_open_without_encoding_flags_on_all_platforms(self):
        """CPY046 is a cross-platform encoding-correctness flag."""
        rule = OpenEncodingRule()
        findings = rule.check(
            parse(
                """
                with open("file.txt") as f:
                    data = f.read()
                """
            ),
            "<test>",
        )
        assert findings
        assert findings[0].rule_id == "CPY046"

    def test_os_fork_flag_is_informational_on_all_platforms(self):
        """PPY039 flags os.fork() regardless of host OS."""
        rule = OsForkRule()
        findings = rule.check(
            parse(
                """
                import os
                pid = os.fork()
                """
            ),
            "<test>",
        )
        assert findings
        assert findings[0].rule_id == "PPY039"

    @pytest.mark.parametrize(
        "src",
        [
            'p = PurePath("CON")\np.is_reserved()\n',
            'from pathlib import PurePath as PP\np = PP("nul")\np.is_reserved()\n',
            "import pathlib\np = pathlib.PurePath('auux')\np.is_reserved()\n",
        ],
        ids=["bare-name", "aliased-import", "module-attr"],
    )
    def test_purepath_variants_consistent_across_platforms(self, src):
        rule = PurePathIsReservedRule()
        findings = rule.check(parse(src), "<test>")
        assert findings

    @pytest.mark.parametrize(
        "src,expected",
        [
            ('open("f.txt")\n', True),
            ('open("f.txt", "w")\n', True),
            ('open("f.txt", encoding=None)\n', False),
            ("fp = open('data.csv')\n", True),
            ("open('x', encoding='utf-8')\n", False),
            ("open('x', 'rb')\n", False),
        ],
        ids=[
            "no-enc",
            "text-mode",
            "none-encoding",
            "assigned",
            "explicit-utf8",
            "binary",
        ],
    )
    def test_open_encoding_variants_consistent_across_platforms(self, src, expected):
        rule = OpenEncodingRule()
        findings = rule.check(parse(src), "<test>")
        # CPY046 flags reliance on the platform default encoding. It must
        # behave identically on every OS: explicit encoding, binary mode,
        # and encoding=None are safe; omitted/None-typed defaults flag.
        assert bool(findings) is expected

    def test_platform_is_some_known_os(self):
        # Guard against a future assumption about a specific host.
        assert os.name in {"posix", "nt"}


class TestPlatformMetadata:
    def test_target_config_platform_default(self):
        from pyrift.targets import TargetConfig

        cfg = TargetConfig()
        assert cfg.platform is None

    def test_platform_metadata_roundtrip(self):
        from pyrift.targets import TargetConfig

        cfg = TargetConfig(minimum=None, maximum=None, platform="windows")
        assert cfg.platform == "windows"