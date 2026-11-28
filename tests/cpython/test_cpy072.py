"""Tests for CPY072 — importlib.abc resource classes deprecated 3.12, removed 3.14."""
import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy072_importlib_abc_resource import ImportlibAbcResourceRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY072:
    rule = ImportlibAbcResourceRule()

    # ------------------------------------------------------------------
    # True-positive: from-import detection (all three classes)
    # ------------------------------------------------------------------

    def test_detects_resource_reader_import(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY072"
        assert findings[0].severity == Severity.ERROR

    def test_detects_traversable_import(self):
        findings = run(self.rule, "from importlib.abc import Traversable")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY072"

    def test_detects_traversable_resources_import(self):
        findings = run(self.rule, "from importlib.abc import TraversableResources")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY072"

    def test_detects_multiple_imports_same_line(self):
        """Alias-level positions give separate (line, col) so both fire."""
        findings = run(
            self.rule,
            "from importlib.abc import ResourceReader, TraversableResources",
        )
        assert len(findings) == 2

    def test_detects_all_three_separate_lines(self):
        src = (
            "from importlib.abc import ResourceReader\n"
            "from importlib.abc import Traversable\n"
            "from importlib.abc import TraversableResources\n"
        )
        findings = run(self.rule, src)
        assert len(findings) == 3

    # ------------------------------------------------------------------
    # True-positive: from-import with alias
    # ------------------------------------------------------------------

    def test_detects_resource_reader_import_alias(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader as RR")
        assert len(findings) == 1

    def test_detects_traversable_import_alias(self):
        findings = run(self.rule, "from importlib.abc import Traversable as T")
        assert len(findings) == 1

    # ------------------------------------------------------------------
    # True-positive: attribute-access form
    # ------------------------------------------------------------------

    def test_detects_attribute_resource_reader(self):
        findings = run(
            self.rule,
            "import importlib.abc\nimportlib.abc.ResourceReader",
        )
        assert len(findings) == 1

    def test_detects_attribute_traversable(self):
        findings = run(
            self.rule,
            "import importlib.abc\nimportlib.abc.Traversable",
        )
        assert len(findings) == 1

    def test_detects_attribute_traversable_resources(self):
        findings = run(
            self.rule,
            "import importlib.abc\nimportlib.abc.TraversableResources",
        )
        assert len(findings) == 1

    # ------------------------------------------------------------------
    # True-negative: correct replacement (importlib.resources.abc)
    # ------------------------------------------------------------------

    def test_clean_importlib_resources_abc(self):
        """importlib.resources.abc is the correct replacement — must NOT fire."""
        findings = run(
            self.rule,
            "from importlib.resources.abc import TraversableResources",
        )
        assert len(findings) == 0

    def test_clean_importlib_resources_abc_traversable(self):
        findings = run(
            self.rule,
            "from importlib.resources.abc import Traversable",
        )
        assert len(findings) == 0

    def test_clean_importlib_resources_abc_resource_reader(self):
        findings = run(
            self.rule,
            "from importlib.resources.abc import ResourceReader",
        )
        assert len(findings) == 0

    # ------------------------------------------------------------------
    # True-negative: safe importlib.abc usage
    # ------------------------------------------------------------------

    def test_clean_unrelated_import(self):
        findings = run(self.rule, "from importlib.abc import Loader")
        assert len(findings) == 0

    def test_clean_unrelated_attribute(self):
        findings = run(self.rule, "other.abc.ResourceReader")
        assert len(findings) == 0

    def test_clean_resource_contents_not_a_real_class(self):
        """ResourceContents never existed in CPython — must NOT fire."""
        findings = run(self.rule, "from importlib.abc import ResourceContents")
        assert len(findings) == 0

    def test_clean_no_importlib_at_all(self):
        findings = run(self.rule, "x = 1 + 2\nprint(x)\n")
        assert len(findings) == 0

    def test_clean_empty_file(self):
        findings = run(self.rule, "")
        assert len(findings) == 0

    # ------------------------------------------------------------------
    # Suggestion / description checks
    # ------------------------------------------------------------------

    def test_suggestion_mentions_resources_abc(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert "importlib.resources.abc" in findings[0].suggestion

    def test_suggestion_names_specific_class(self):
        findings = run(self.rule, "from importlib.abc import Traversable")
        assert "Traversable" in findings[0].suggestion

    def test_description_mentions_deprecated(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert "deprecated" in findings[0].description.lower()

    def test_description_mentions_removed(self):
        findings = run(self.rule, "from importlib.abc import TraversableResources")
        assert "removed" in findings[0].description.lower()

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert "3.14" in findings[0].description

    def test_docs_url_points_to_3_14_removed(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert "3.14" in findings[0].docs_url
        assert "removed" in findings[0].docs_url

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def test_affected_from_is_3_12(self):
        """DeprecationWarning added in 3.12 (gh-93963) — rule fires from 3.12."""
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert findings[0].affected_from == "3.12"

    def test_affected_until_is_empty(self):
        """Removed in 3.14 — no upper bound (fires forever from 3.12 onward)."""
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert findings[0].affected_until == ""

    def test_severity_is_error(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert findings[0].severity == Severity.ERROR