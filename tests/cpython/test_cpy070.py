"""Tests for CPY070 — asyncio event loop policy deprecated 3.14, removed 3.16."""
import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy070_asyncio_event_loop_policy import (
    AsyncioEventLoopPolicyRule,
)


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY070:
    rule = AsyncioEventLoopPolicyRule()

    # ------------------------------------------------------------------
    # True-positive: attribute calls (policy functions)
    # ------------------------------------------------------------------

    def test_detects_get_event_loop_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.get_event_loop_policy()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY070"
        assert findings[0].severity == Severity.WARNING

    def test_detects_set_event_loop_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.set_event_loop_policy(policy)")
        assert len(findings) == 1

    # ------------------------------------------------------------------
    # True-positive: attribute access (policy classes)
    # ------------------------------------------------------------------

    def test_detects_default_event_loop_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.DefaultEventLoopPolicy")
        assert len(findings) == 1

    def test_detects_abstract_event_loop_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.AbstractEventLoopPolicy")
        assert len(findings) == 1

    def test_detects_windows_selector_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.WindowsSelectorEventLoopPolicy")
        assert len(findings) == 1

    def test_detects_windows_proactor_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.WindowsProactorEventLoopPolicy")
        assert len(findings) == 1

    # ------------------------------------------------------------------
    # True-positive: from-import detection (all six names)
    # ------------------------------------------------------------------

    def test_detects_from_import_get_policy(self):
        findings = run(self.rule, "from asyncio import get_event_loop_policy")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY070"

    def test_detects_from_import_set_policy(self):
        findings = run(self.rule, "from asyncio import set_event_loop_policy")
        assert len(findings) == 1

    def test_detects_from_import_abstract_policy(self):
        findings = run(self.rule, "from asyncio import AbstractEventLoopPolicy")
        assert len(findings) == 1

    def test_detects_from_import_default_policy(self):
        findings = run(self.rule, "from asyncio import DefaultEventLoopPolicy")
        assert len(findings) == 1

    def test_detects_from_import_windows_selector_policy(self):
        findings = run(self.rule, "from asyncio import WindowsSelectorEventLoopPolicy")
        assert len(findings) == 1

    def test_detects_from_import_windows_proactor_policy(self):
        findings = run(self.rule, "from asyncio import WindowsProactorEventLoopPolicy")
        assert len(findings) == 1

    # ------------------------------------------------------------------
    # True-positive: from-import with alias
    # ------------------------------------------------------------------

    def test_detects_from_import_alias_get_policy(self):
        findings = run(self.rule, "from asyncio import get_event_loop_policy as get_pol")
        assert len(findings) == 1

    def test_detects_from_import_alias_abstract_policy(self):
        findings = run(self.rule, "from asyncio import AbstractEventLoopPolicy as ALP")
        assert len(findings) == 1

    # ------------------------------------------------------------------
    # True-positive: instantiation of policy class
    # ------------------------------------------------------------------

    def test_detects_default_policy_instantiation(self):
        findings = run(self.rule, "import asyncio\npol = asyncio.DefaultEventLoopPolicy()")
        assert len(findings) == 1

    # ------------------------------------------------------------------
    # True-positive: multiple deprecated names in one file
    # ------------------------------------------------------------------

    def test_multiple_deprecated_names_one_finding_each(self):
        src = (
            "import asyncio\n"
            "asyncio.get_event_loop_policy()\n"
            "asyncio.set_event_loop_policy(None)\n"
        )
        findings = run(self.rule, src)
        assert len(findings) == 2

    # ------------------------------------------------------------------
    # True-negative: safe asyncio usage
    # ------------------------------------------------------------------

    def test_clean_asyncio_run(self):
        findings = run(self.rule, "import asyncio\nasyncio.run(main())")
        assert len(findings) == 0

    def test_clean_asyncio_runner(self):
        findings = run(self.rule, "import asyncio\nasyncio.Runner()")
        assert len(findings) == 0

    def test_clean_unrelated_attribute(self):
        findings = run(self.rule, "other.get_event_loop_policy()")
        assert len(findings) == 0

    def test_clean_unrelated_import(self):
        findings = run(self.rule, "from asyncio import run, create_task")
        assert len(findings) == 0

    def test_clean_no_asyncio_at_all(self):
        findings = run(self.rule, "x = 1 + 2\nprint(x)\n")
        assert len(findings) == 0

    def test_clean_empty_file(self):
        findings = run(self.rule, "")
        assert len(findings) == 0

    # ------------------------------------------------------------------
    # Suggestion / description checks
    # ------------------------------------------------------------------

    def test_suggestion_mentions_asyncio_run(self):
        findings = run(self.rule, "import asyncio\nasyncio.get_event_loop_policy()")
        assert "asyncio.run" in findings[0].suggestion

    def test_suggestion_mentions_loop_factory(self):
        findings = run(self.rule, "import asyncio\nasyncio.get_event_loop_policy()")
        assert "loop_factory" in findings[0].suggestion

    def test_description_mentions_deprecated(self):
        findings = run(self.rule, "import asyncio\nasyncio.get_event_loop_policy()")
        assert "deprecated" in findings[0].description.lower()

    def test_description_mentions_deprecated_version(self):
        findings = run(self.rule, "import asyncio\nasyncio.get_event_loop_policy()")
        assert "3.14" in findings[0].description

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "import asyncio\nasyncio.get_event_loop_policy()")
        assert "3.16" in findings[0].description

    def test_docs_url_points_to_whatsnew_3_14(self):
        findings = run(self.rule, "from asyncio import get_event_loop_policy")
        assert "3.14" in findings[0].docs_url

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def test_affected_from_is_3_14(self):
        findings = run(self.rule, "from asyncio import get_event_loop_policy")
        assert findings[0].affected_from == "3.14"

    def test_affected_until_is_3_16(self):
        """Deprecated 3.14, removed 3.16 — fires through 3.16 inclusive."""
        findings = run(self.rule, "from asyncio import get_event_loop_policy")
        assert findings[0].affected_until == "3.16"

    def test_severity_is_warning(self):
        findings = run(self.rule, "from asyncio import get_event_loop_policy")
        assert findings[0].severity == Severity.WARNING