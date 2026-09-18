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

    def test_aliased_import_still_detected(self):
        """Exercises the symbol-resolution integration (item #7)."""
        findings = run(
            self.rule,
            "import functools as ft\nft.reduce(function=f, sequence=xs)",
        )
        assert len(findings) == 1

    def test_unrelated_bare_reduce_not_flagged(self):
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
