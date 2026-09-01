import ast
import textwrap

from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: WeakrefProxyRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY004:
    rule = WeakrefProxyRule()

    def test_detects_weakref_proxy(self):
        findings = run(
            self.rule,
            """
            import weakref
            p = weakref.proxy(obj)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY004"

    def test_detects_aliased_weakref_proxy(self):
        findings = run(
            self.rule,
            """
            import weakref as wr
            p = wr.proxy(obj)
            """,
        )

        assert len(findings) == 1

    def test_detects_direct_proxy_import(self):
        findings = run(
            self.rule,
            """
            from weakref import proxy
            p = proxy(obj)
            """,
        )

        assert len(findings) == 1

    def test_detects_aliased_proxy_import(self):
        findings = run(
            self.rule,
            """
            from weakref import proxy as make_proxy
            p = make_proxy(obj)
            """,
        )

        assert len(findings) == 1

    def test_detects_multiple_proxies(self):
        findings = run(
            self.rule,
            """
            import weakref
            first = weakref.proxy(obj)
            second = weakref.proxy(other)
            """,
        )

        assert len(findings) == 2

    def test_clean_weakref_ref(self):
        findings = run(
            self.rule,
            """
            import weakref
            r = weakref.ref(obj)
            """,
        )

        assert len(findings) == 0

    def test_clean_unrelated_proxy_method(self):
        findings = run(
            self.rule,
            """
            import weakref
            obj.proxy(value)
            """,
        )

        assert len(findings) == 0

    def test_clean_unrelated_module_proxy(self):
        findings = run(
            self.rule,
            """
            import other
            p = other.proxy(obj)
            """,
        )

        assert len(findings) == 0

    def test_clean_bare_proxy_without_import(self):
        findings = run(
            self.rule,
            "proxy(obj)",
        )

        assert len(findings) == 0

    def test_suggestion_mentions_ref(self):
        findings = run(
            self.rule,
            """
            import weakref
            weakref.proxy(obj)
            """,
        )

        assert "ref()" in findings[0].suggestion