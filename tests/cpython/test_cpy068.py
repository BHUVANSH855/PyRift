"""Tests for CPY068 — typing.no_type_check_decorator deprecated 3.13, removed 3.15."""
import ast

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy068_typing_no_type_check_decorator import (
    TypingNoTypeCheckDecoratorRule,
)


def run(rule, src: str):
    tree = ast.parse(src)
    return rule.check(tree, "test.py")


class TestCPY068:
    rule = TypingNoTypeCheckDecoratorRule()

    # ------------------------------------------------------------------ imports

    def test_detects_import(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY068"
        assert findings[0].severity == Severity.WARNING

    def test_detects_typing_extensions_import(self):
        findings = run(
            self.rule,
            "from typing_extensions import no_type_check_decorator",
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY068"

    def test_import_among_others(self):
        # Flagged even when imported alongside other names
        findings = run(
            self.rule,
            "from typing import Any, no_type_check_decorator, Optional",
        )
        assert len(findings) == 1

    # ------------------------------------------------------------------ attribute access

    def test_detects_attribute_access(self):
        src = "@typing.no_type_check_decorator\ndef f(): pass"
        findings = run(self.rule, src)
        assert len(findings) >= 1
        assert findings[0].rule_id == "CPY068"

    def test_detects_typing_extensions_attribute_access(self):
        src = "@typing_extensions.no_type_check_decorator\ndef f(): pass"
        findings = run(self.rule, src)
        assert len(findings) >= 1
        assert findings[0].rule_id == "CPY068"

    # ------------------------------------------------------------------ clean cases

    def test_clean_no_type_check(self):
        """typing.no_type_check (without _decorator) is NOT deprecated."""
        findings = run(self.rule, "from typing import no_type_check")
        assert len(findings) == 0

    def test_clean_no_type_check_attribute(self):
        findings = run(self.rule, "@typing.no_type_check\ndef f(): pass")
        assert len(findings) == 0

    def test_clean_unrelated_import(self):
        findings = run(self.rule, "from typing import Any, Optional")
        assert len(findings) == 0

    def test_unrelated_module_not_flagged(self):
        # Only typing/typing_extensions are in scope
        findings = run(
            self.rule,
            "from mylib import no_type_check_decorator",
        )
        assert len(findings) == 0

    def test_empty_file(self):
        assert run(self.rule, "") == []

    # ------------------------------------------------------------------ suggestion / description

    def test_suggestion_mentions_no_type_check(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert "no_type_check" in findings[0].suggestion

    def test_description_mentions_deprecated(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        desc = findings[0].description.lower()
        assert "deprecated" in desc or "removed" in desc

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert "3.15" in findings[0].description

    def test_docs_url_points_to_3_15_removed(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert "3.15" in findings[0].docs_url
        assert "removed" in findings[0].docs_url

    # ------------------------------------------------------------------ metadata

    def test_affected_from_is_3_13(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert findings[0].affected_from == "3.13"

    def test_affected_until_is_empty(self):
        """Removal rules carry no upper bound — fires forever from 3.13 onward."""
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert findings[0].affected_until == ""

    def test_severity_is_warning(self):
        findings = run(self.rule, "from typing import no_type_check_decorator")
        assert findings[0].severity == Severity.WARNING