"""
Tests for pyrift.analysis.imports.
"""
from __future__ import annotations

import ast
import textwrap

from pyrift.analysis.imports import collect_dynamic_imports, collect_imports


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


class TestHasNameFrom:
    def test_true_when_name_present(self):
        imp = collect_imports(parse("from tomllib import load"))
        assert imp.has_name_from("tomllib", "load")

    def test_false_when_name_absent(self):
        imp = collect_imports(parse("from tomllib import load"))
        assert not imp.has_name_from("tomllib", "loads")

    def test_false_when_module_different(self):
        imp = collect_imports(parse("from json import load"))
        assert not imp.has_name_from("tomllib", "load")


class TestAliasFor:
    def test_returns_explicit_alias(self):
        imp = collect_imports(parse("import tomllib as tl"))
        assert imp.alias_for("tomllib") == "tl"

    def test_returns_module_tail_when_no_alias(self):
        imp = collect_imports(parse("import tomllib"))
        assert imp.alias_for("tomllib") == "tomllib"

    def test_returns_module_tail_for_submodule(self):
        imp = collect_imports(parse("import collections.abc"))
        assert imp.alias_for("collections.abc") == "abc"

    def test_returns_none_for_unimported_module(self):
        imp = collect_imports(parse("import json"))
        assert imp.alias_for("tomllib") is None


class TestByStatementFilter:
    def test_filters_by_module(self):
        imp = collect_imports(
            parse("import json\nimport tomllib\nfrom tomllib import load")
        )
        # tomllib present in 2 statements.
        assert len(imp.by_statement("tomllib")) == 2
        assert len(imp.by_statement("json")) == 1

    def test_by_statement_no_filter_counts_all_statements(self):
        imp = collect_imports(
            parse("import a\nimport b\nfrom c import x, y")
        )
        # 3 import statements -> 3 entries (multi-name deduped).
        assert len(imp.by_statement()) == 3


class TestGetVersionGuard:
    def test_guarded_import_skipped_when_covered(self):
        imp = collect_imports(
            parse(
                """
                import sys
                if sys.version_info >= (3, 11):
                    import tomllib
                """
            )
        )
        # min_version (3,11): the guard >= (3,11) covers it -> skipped.
        assert imp.get("tomllib", min_version=(3, 11)) == []
        # min_version (3,12): the guard (3,11) does NOT cover (3,12) -> returned.
        assert len(imp.get("tomllib", min_version=(3, 12))) == 1

    def test_unguarded_import_always_returned(self):
        imp = collect_imports(parse("import tomllib"))
        assert len(imp.get("tomllib", min_version=(3, 11))) == 1

    def test_get_dedups_multi_name_from_import(self):
        imp = collect_imports(parse("from tomllib import load, loads"))
        # Single statement -> single entry.
        assert len(imp.get("tomllib")) == 1


class TestVersionGuardExtraction:
    def test_extracts_constant_tuple(self):
        from pyrift.analysis.imports import _extract_version_guard

        tree = parse(
            """
            import sys
            if sys.version_info >= (3, 11):
                import tomllib
            """
        )
        # Find the import node inside the guard.
        import_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                import_node = node
        parent_map = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parent_map[id(child)] = parent
        assert _extract_version_guard(parent_map, import_node) == (3, 11)


class TestCollectDynamicImports:
    def test_detects_importlib_import_module(self):
        found = collect_dynamic_imports(
            parse("m = importlib.import_module('cgi')")
        )
        assert len(found) == 1
        assert found[0].module == "cgi"

    def test_detects_dunder_import(self):
        found = collect_dynamic_imports(
            parse("_ = __import__('telnetlib')")
        )
        assert len(found) == 1
        assert found[0].module == "telnetlib"

    def test_ignores_dynamic_module_name(self):
        found = collect_dynamic_imports(
            parse("m = importlib.import_module(name)")
        )
        assert found == []

    def test_ignores_other_calls(self):
        found = collect_dynamic_imports(
            parse("m = some_module_func('cgi')")
        )
        assert found == []

    def test_does_not_match_importlib_attribute_other_than_import_module(self):
        found = collect_dynamic_imports(
            parse("m = importlib.reload('cgi')")
        )
        assert found == []