"""Tests for CPY078 — functools.reduce() keyword arguments deprecated 3.14, removal scheduled 3.16."""
import ast
import textwrap

from pyrift.finding import Runtime, Severity
from pyrift.rules.cpython.cpy078_functools_reduce_kwargs import (
    FunctoolsReduceKeywordArgsRule,
)


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY078:
    rule = FunctoolsReduceKeywordArgsRule()

    # ------------------------------------------------------------------ #
    # Detection                                                            #
    # ------------------------------------------------------------------ #

    def test_detects_function_and_sequence_as_keywords(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs)",
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY078"
        assert findings[0].severity == Severity.WARNING
        assert findings[0].runtime == Runtime.CPYTHON
        assert findings[0].affected_from == "3.14"
        assert findings[0].affected_until == "3.16"

    def test_detects_sequence_only_as_keyword(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(f, sequence=xs)",
        )
        assert len(findings) == 1

    def test_detects_function_only_as_keyword(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs, initial=0)",
        )
        assert len(findings) == 1

    def test_aliased_import_still_detected(self):
        """import functools as ft — alias tracking via collect_calls."""
        findings = run(
            self.rule,
            "import functools as ft\nft.reduce(function=f, sequence=xs)",
        )
        assert len(findings) == 1

    def test_function_keyword_alone(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs)",
        )
        assert len(findings) == 1
        assert "function" in findings[0].description

    def test_sequence_keyword_alone_description(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(f, sequence=xs)",
        )
        assert len(findings) == 1
        assert "sequence" in findings[0].description

    # ------------------------------------------------------------------ #
    # Negative cases                                                       #
    # ------------------------------------------------------------------ #

    def test_clean_positional_call(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(f, xs)",
        )
        assert len(findings) == 0

    def test_clean_positional_call_with_initial(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(f, xs, 0)",
        )
        assert len(findings) == 0

    def test_clean_initial_as_keyword_is_ok(self):
        """'initial' is NOT in the deprecated list — only 'function'/'sequence'."""
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(f, xs, initial=0)",
        )
        assert len(findings) == 0

    def test_unrelated_bare_reduce_not_flagged(self):
        """Bare reduce() (not from functools) must not fire."""
        findings = run(
            self.rule,
            "reduce(function=f, sequence=xs)",
        )
        assert len(findings) == 0

    def test_shadowed_functools_name_not_flagged(self):
        findings = run(
            self.rule,
            "import functools\n"
            "functools = fake_module()\n"
            "functools.reduce(function=f, sequence=xs)",
        )
        assert len(findings) == 0

    def test_clean_unrelated_module_reduce_call(self):
        findings = run(
            self.rule,
            "import mylib\nmylib.reduce(function=f, sequence=xs)",
        )
        assert len(findings) == 0

    def test_clean_empty_file(self):
        findings = run(self.rule, "")
        assert len(findings) == 0

    # ------------------------------------------------------------------ #
    # Suggestion / metadata correctness                                    #
    # ------------------------------------------------------------------ #

    def test_suggestion_mentions_positional(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs)",
        )
        assert "positionally" in findings[0].suggestion.lower()

    def test_docs_url_points_to_pending_removal_page(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs)",
        )
        assert "pending-removal-in-3.16" in findings[0].docs_url

    def test_description_names_offending_kwargs(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs)",
        )
        desc = findings[0].description
        assert "function" in desc and "sequence" in desc

    def test_description_names_single_offending_kwarg(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(f, sequence=xs)",
        )
        assert "sequence" in findings[0].description

    def test_severity_is_warning(self):
        """Still pending — severity is WARNING, not ERROR."""
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs)",
        )
        assert findings[0].severity == Severity.WARNING

    def test_affected_from_is_3_14(self):
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs)",
        )
        assert findings[0].affected_from == "3.14"

    def test_affected_until_is_3_16(self):
        """Scheduled for removal in 3.16 — fires through 3.16 inclusive."""
        findings = run(
            self.rule,
            "import functools\nfunctools.reduce(function=f, sequence=xs)",
        )
        assert findings[0].affected_until == "3.16"