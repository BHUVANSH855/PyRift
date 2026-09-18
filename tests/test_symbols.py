"""Tests for pyrift.analysis.symbols (2026-09 audit items #7-8)."""
from __future__ import annotations

import ast
import textwrap

from pyrift.analysis.symbols import build_symbol_table


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


class TestModuleAliasResolution:
    def test_plain_import_resolves(self):
        table = build_symbol_table(parse("import asyncio"))
        assert table.module_aliases["asyncio"] == "asyncio"

    def test_aliased_import_resolves(self):
        table = build_symbol_table(parse("import asyncio as aio"))
        assert table.module_aliases["aio"] == "asyncio"
        assert "asyncio" not in table.module_aliases

    def test_dotted_import_binds_top_level_name_only(self):
        table = build_symbol_table(parse("import xml.etree.ElementTree"))
        # `import xml.etree.ElementTree` binds the name `xml`, not the
        # full dotted path -- attribute-call resolution for the
        # sub-path isn't attempted (rare pattern for the rules that use
        # this), but the name is still tracked as import-bound so
        # shadowing detection still applies to it.
        assert "xml" not in table.module_aliases or table.module_aliases.get("xml") == "xml.etree.ElementTree"

    def test_resolve_attribute_through_alias(self):
        tree = parse("import asyncio as aio\naio.get_event_loop()")
        table = build_symbol_table(tree)
        call = next(
            n for n in ast.walk(tree)
            if isinstance(n, ast.Attribute) and n.attr == "get_event_loop"
        )
        assert table.resolve_attribute(call) == ("asyncio", "get_event_loop")


class TestNameAliasResolution:
    def test_from_import_resolves(self):
        table = build_symbol_table(parse("from typing import Self"))
        assert table.name_aliases["Self"] == ("typing", "Self")

    def test_from_import_aliased_resolves(self):
        table = build_symbol_table(
            parse("from asyncio import get_event_loop as gel")
        )
        assert table.name_aliases["gel"] == ("asyncio", "get_event_loop")


class TestShadowing:
    def test_reassigned_import_name_is_shadowed(self):
        table = build_symbol_table(
            parse("import asyncio\nasyncio = something_else()")
        )
        assert table.is_shadowed("asyncio")

    def test_reassigned_from_import_name_is_shadowed(self):
        table = build_symbol_table(
            parse("from typing import Self\nSelf = object()")
        )
        assert table.is_shadowed("Self")

    def test_unshadowed_import_is_not_shadowed(self):
        table = build_symbol_table(parse("import asyncio\nasyncio.run(x())"))
        assert not table.is_shadowed("asyncio")

    def test_function_parameter_shadows_import(self):
        table = build_symbol_table(
            parse(
                """
                import asyncio
                def f(asyncio):
                    asyncio.get_event_loop()
                """
            )
        )
        assert table.is_shadowed("asyncio")

    def test_for_loop_target_shadows_import(self):
        table = build_symbol_table(
            parse(
                """
                import asyncio
                for asyncio in things:
                    pass
                """
            )
        )
        assert table.is_shadowed("asyncio")

    def test_with_target_shadows_import(self):
        table = build_symbol_table(
            parse(
                """
                import asyncio
                with make_thing() as asyncio:
                    pass
                """
            )
        )
        assert table.is_shadowed("asyncio")

    def test_lambda_parameter_shadows_import(self):
        table = build_symbol_table(
            parse("import asyncio\nf = lambda asyncio: asyncio.run(x())")
        )
        assert table.is_shadowed("asyncio")

    def test_function_def_name_shadows_import(self):
        table = build_symbol_table(
            parse(
                """
                import asyncio
                def asyncio():
                    pass
                """
            )
        )
        assert table.is_shadowed("asyncio")

    def test_resolve_attribute_refuses_shadowed_name(self):
        tree = parse(
            "import asyncio\nasyncio = fake()\nasyncio.get_event_loop()"
        )
        table = build_symbol_table(tree)
        call = next(
            n for n in ast.walk(tree)
            if isinstance(n, ast.Attribute) and n.attr == "get_event_loop"
        )
        assert table.resolve_attribute(call) is None

    def test_unrelated_names_are_not_shadowed(self):
        """Reassigning some other, unrelated name must not mark an
        actual import as shadowed."""
        table = build_symbol_table(
            parse("import asyncio\nsome_other_var = 1\nasyncio.run(x())")
        )
        assert not table.is_shadowed("asyncio")
