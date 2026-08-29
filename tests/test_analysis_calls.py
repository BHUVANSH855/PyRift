import ast

from pyrift.analysis.calls import (
    collect_calls,
    get_keyword_value,
    has_keyword_arg,
)


def parse(src: str) -> ast.AST:
    return ast.parse(src)


class TestCollectCalls:
    def test_bare_function_call(self):
        results = collect_calls(parse("open('file.txt')"), "open")
        assert len(results) == 1
        assert results[0].func_name == "open"
        assert results[0].module is None

    def test_module_method_call(self):
        results = collect_calls(parse("asyncio.get_event_loop()"),
                                "get_event_loop", module="asyncio")
        assert len(results) == 1
        assert results[0].module == "asyncio"

    def test_no_match(self):
        results = collect_calls(parse("os.path.join('a', 'b')"),
                                "open")
        assert len(results) == 0

    def test_wrong_module(self):
        results = collect_calls(parse("os.open('file')"),
                                "open", module="asyncio")
        assert len(results) == 0

    def test_bare_not_module(self):
        # Bare call should not match when module specified
        results = collect_calls(parse("get_event_loop()"),
                                "get_event_loop", module="asyncio")
        assert len(results) == 0

    def test_call_with_args(self):
        results = collect_calls(parse("open('file.txt', 'r')"), "open")
        assert len(results) == 1
        assert len(results[0].args) == 2

    def test_call_with_kwargs(self):
        results = collect_calls(
            parse("open('file.txt', encoding='utf-8')"), "open"
        )
        assert len(results) == 1
        assert "encoding" in results[0].kwargs


class TestHasKeywordArg:
    def test_has_keyword(self):
        tree = ast.parse("open('f', encoding='utf-8')")
        call = tree.body[0].value
        assert has_keyword_arg(call, "encoding") is True

    def test_missing_keyword(self):
        tree = ast.parse("open('f')")
        call = tree.body[0].value
        assert has_keyword_arg(call, "encoding") is False


class TestGetKeywordValue:
    def test_gets_value(self):
        tree = ast.parse("open('f', encoding='utf-8')")
        call = tree.body[0].value
        val = get_keyword_value(call, "encoding")
        assert val is not None
        assert isinstance(val, ast.Constant)
        assert val.value == "utf-8"

    def test_returns_none_when_missing(self):
        tree = ast.parse("open('f')")
        call = tree.body[0].value
        assert get_keyword_value(call, "encoding") is None

    def test_doublestar_spread_not_in_kwargs(self):
        """**kwargs spread (arg=None) should not match named keyword lookup."""
        tree = ast.parse("open('f', **extra)")
        call = tree.body[0].value
        assert has_keyword_arg(call, "encoding") is False
        assert get_keyword_value(call, "extra") is None

    def test_keyword_only_args(self):
        """Keyword-only args (after *) appear as regular keyword args."""
        tree = ast.parse("f(x, encoding='utf-8', errors='strict')")
        call = tree.body[0].value
        assert has_keyword_arg(call, "encoding")
        assert has_keyword_arg(call, "errors")
        assert get_keyword_value(call, "encoding").value == "utf-8"
        assert get_keyword_value(call, "errors").value == "strict"

    def test_nested_call_detection(self):
        """collect_calls finds calls inside nested expressions."""
        tree = ast.parse("print(open('f').read())")
        results = collect_calls(tree, "open")
        assert len(results) == 1
        results = collect_calls(tree, "print")
        assert len(results) == 1

    def test_multiple_calls_same_function(self):
        """Multiple calls to the same function are all collected."""
        tree = ast.parse("open('a'); open('b')")
        results = collect_calls(tree, "open")
        assert len(results) == 2

    def test_lambda_call_not_collected(self):
        """Lambda invocations are not collected by walk."""
        tree = ast.parse("(lambda: open('f'))()")
        # The Call wraps a Lambda; open() inside the lambda body should be found.
        results = collect_calls(tree, "open")
        assert len(results) == 1