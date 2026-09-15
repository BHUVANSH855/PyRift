import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy069_asyncio_iscoroutinefunction import (
    AsyncioIscoroutinefunctionRule,
)


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY069:
    rule = AsyncioIscoroutinefunctionRule()

    def test_detects_import(self):
        findings = run(self.rule, "from asyncio import iscoroutinefunction")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY069"
        assert findings[0].severity == Severity.WARNING

    def test_detects_call(self):
        findings = run(
            self.rule,
            "import asyncio\nasyncio.iscoroutinefunction(func)",
        )
        assert len(findings) == 1

    def test_detects_module_alias(self):
        findings = run(
            self.rule,
            "import asyncio as aio\naio.iscoroutinefunction(func)",
        )
        assert len(findings) == 1

    def test_detects_from_import_alias(self):
        findings = run(
            self.rule,
            "from asyncio import iscoroutinefunction as is_cf\nis_cf(func)",
        )
        assert len(findings) == 1

    def test_ignores_shadowed_asyncio_module(self):
        findings = run(
            self.rule,
            "import asyncio\n"
            "asyncio = FakeAsyncio()\n"
            "asyncio.iscoroutinefunction(func)",
        )
        assert len(findings) == 0

    def test_ignores_function_local_shadowing(self):
        findings = run(
            self.rule,
            "import asyncio\n"
            "\n"
            "def check():\n"
            "    asyncio = FakeAsyncio()\n"
            "    asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 0

    def test_detects_function_local_asyncio_import(self):
        findings = run(
            self.rule,
            "def check():\n    import asyncio\n    asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 1

    def test_ignores_shadowed_from_import(self):
        findings = run(
            self.rule,
            "from asyncio import iscoroutinefunction\n"
            "\n"
            "iscoroutinefunction = fake_function\n"
            "iscoroutinefunction(func)\n",
        )
        assert len(findings) == 0

    def test_detects_nested_function_using_module_import(self):
        findings = run(
            self.rule,
            "import asyncio\n"
            "\n"
            "def outer():\n"
            "    def inner():\n"
            "        asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 1

    def test_clean_unrelated_attribute(self):
        findings = run(
            self.rule,
            "other.iscoroutinefunction(func)",
        )
        assert len(findings) == 0

    def test_clean_inspect_iscoroutinefunction(self):
        findings = run(
            self.rule,
            "import inspect\ninspect.iscoroutinefunction(func)",
        )
        assert len(findings) == 0

    def test_suggestion_mentions_inspect(self):
        findings = run(
            self.rule,
            "import asyncio\nasyncio.iscoroutinefunction(func)",
        )
        assert "inspect" in findings[0].suggestion

    def test_ignores_module_level_rebinding(self):
        findings = run(
            self.rule,
            "from asyncio import iscoroutinefunction\n"
            "iscoroutinefunction = fake_function\n"
            "iscoroutinefunction(func)\n",
        )
        assert len(findings) == 0

    def test_ignores_function_parameter_shadowing(self):
        findings = run(
            self.rule,
            "import asyncio\n"
            "\n"
            "def check(asyncio):\n"
            "    asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 0

    def test_ignores_function_local_rebinding(self):
        findings = run(
            self.rule,
            "import asyncio\n"
            "\n"
            "def check():\n"
            "    asyncio = fake_module\n"
            "    asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 0

    def test_detects_function_local_module_alias(self):
        findings = run(
            self.rule,
            "def check():\n"
            "    import asyncio as aio\n"
            "    aio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 1

    def test_detects_function_local_symbol_alias(self):
        findings = run(
            self.rule,
            "def check():\n"
            "    from asyncio import iscoroutinefunction as is_cf\n"
            "    is_cf(func)\n",
        )
        assert len(findings) == 1

    def test_ignores_inspect_symbol(self):
        findings = run(
            self.rule,
            "from inspect import iscoroutinefunction\niscoroutinefunction(func)\n",
        )
        assert len(findings) == 0

    def test_ignores_unrelated_asyncio_import(self):
        findings = run(
            self.rule,
            "from asyncio import create_task\ncreate_task(func)\n",
        )
        assert len(findings) == 0

    def test_ignores_nested_function_shadowing(self):
        findings = run(
            self.rule,
            "import asyncio\n"
            "\n"
            "def outer():\n"
            "    def inner(asyncio):\n"
            "        asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 0

    def test_detects_outer_module_alias_inside_nested_function(self):
        findings = run(
            self.rule,
            "import asyncio\n"
            "\n"
            "def outer():\n"
            "    def inner():\n"
            "        asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 1

    def test_ignores_class_attribute_shadowing(self):
        findings = run(
            self.rule,
            "import asyncio\n"
            "\n"
            "class Example:\n"
            "    asyncio = fake_module\n"
            "    asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 0

    def test_detects_module_alias_in_class_without_shadowing(self):
        findings = run(
            self.rule,
            "import asyncio\n\nclass Example:\n    asyncio.iscoroutinefunction(func)\n",
        )
        assert len(findings) == 1

    def test_import_then_rebind_inside_function_is_ignored(self):
        findings = run(
            self.rule,
            "def check():\n"
            "    from asyncio import iscoroutinefunction\n"
            "    iscoroutinefunction = fake_function\n"
            "    iscoroutinefunction(func)\n",
        )
        assert len(findings) == 0
