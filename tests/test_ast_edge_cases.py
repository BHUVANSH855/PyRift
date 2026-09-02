import ast
import textwrap


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule_cls, src):
    return rule_cls().check(parse(src), "<test>")


class TestAliasedImports:
    def test_weakref_proxy_alias(self):
        """`from weakref import proxy as wp` is detected through the alias."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        src = """
        from weakref import proxy as wp
        wp(obj)
        """
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY004"


class TestImportsInsideFunctions:
    def test_proxy_inside_function(self):
        """Imported proxy() call inside a function triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        src = """
        def make_proxy(obj):
            from weakref import proxy
            return proxy(obj)
        """
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1


class TestLambdaPatterns:
    def test_lambda_with_proxy_call(self):
        """Imported proxy() inside a lambda triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        src = """
        from weakref import proxy
        make = lambda obj: proxy(obj)
        """
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1


class TestComprehensions:
    def test_dict_comp_with_proxy(self):
        """Imported proxy() inside a dict comprehension triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        src = """
        from weakref import proxy
        proxies = {k: proxy(v) for k, v in items}
        """
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1

    def test_generator_expr_with_proxy(self):
        """Imported proxy() inside a generator expression triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        src = """
        from weakref import proxy
        gen = (proxy(obj) for obj in objs)
        """
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1


class TestDecoratorPatterns:
    def test_decorator_with_proxy(self):
        """Imported proxy() call in a decorator triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        src = """
        from weakref import proxy

        @proxy(obj)
        def wrapper():
            pass
        """
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1


class TestMatchCasePatterns:
    def test_match_with_proxy_in_case(self):
        """Imported proxy() in match/case triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        src = """
        from weakref import proxy

        match action:
            case "wrap":
                p = proxy(obj)
        """
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1


class TestMultiLineCalls:
    def test_multiline_proxy(self):
        """Imported proxy() in a multi-line call triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        src = """
        from weakref import proxy

        p = proxy(
            obj
        )
        """
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1