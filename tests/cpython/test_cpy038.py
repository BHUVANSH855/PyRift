import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy038_asyncio_get_event_loop import AsyncioGetEventLoopRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY038:
    rule = AsyncioGetEventLoopRule()

    def test_detects_get_event_loop(self):
        findings = run(self.rule,
            "import asyncio\nloop = asyncio.get_event_loop()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY038"
        assert findings[0].severity == Severity.ERROR

    def test_clean_asyncio_run(self):
        findings = run(self.rule,
            "import asyncio\nasyncio.run(main())")
        assert len(findings) == 0

    def test_suggestion_mentions_asyncio_run(self):
        findings = run(self.rule, "asyncio.get_event_loop()")
        assert "asyncio.run" in findings[0].suggestion.lower() or \
               "run" in findings[0].suggestion.lower()
    def test_detects_aliased_import(self):
        """Item #7 (2026-09 audit): `import asyncio as aio` used to be a
        documented false negative (see benchmark/run_benchmark.py)."""
        findings = run(
            self.rule,
            "import asyncio as aio\nloop = aio.get_event_loop()",
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY038"

    def test_does_not_flag_shadowed_module_name(self):
        """Item #8 (2026-09 audit): if `asyncio` is reassigned to
        something else in the file, a later `asyncio.get_event_loop()`
        must not be attributed to the real asyncio module."""
        findings = run(
            self.rule,
            "import asyncio\n"
            "asyncio = _make_fake_asyncio()\n"
            "asyncio.get_event_loop()",
        )
        assert len(findings) == 0

    def test_does_not_flag_different_module_aliased_to_same_name(self):
        """`import foo as asyncio; asyncio.get_event_loop()` refers to
        `foo.get_event_loop`, not `asyncio.get_event_loop` -- the local
        name happening to read "asyncio" must not cause a false match."""
        findings = run(
            self.rule,
            "import foo as asyncio\nasyncio.get_event_loop()",
        )
        assert len(findings) == 0

    def test_from_import_aliased_call_style_unaffected(self):
        """Sanity check: an unrelated function with the same bare name,
        imported directly (no module qualifier), is not something this
        rule claims to check -- module-qualified detection only."""
        findings = run(
            self.rule,
            "from somewhere import get_event_loop\nget_event_loop()",
        )
        assert len(findings) == 0
