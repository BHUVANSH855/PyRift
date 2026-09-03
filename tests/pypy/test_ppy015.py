import ast
import textwrap

from pyrift.rules.pypy.ppy015_generator_gc import GeneratorGCRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestPPY015:
    rule = GeneratorGCRule()

    def test_detects_yield_in_try(self):
        src = """
        def gen():
            try:
                yield value
            finally:
                cleanup()
        """
        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY015"

    def test_detects_yield_in_with(self):
        src = """
        def gen():
            with open("file") as f:
                yield f.read()
        """
        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_clean_generator_no_try(self):
        src = """
        def gen():
            for i in range(10):
                yield i
        """
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_suggestion_mentions_close(self):
        src = """
        def gen():
            try:
                yield 1
            finally:
                pass
        """
        findings = run(self.rule, src)

        assert "close" in findings[0].suggestion.lower()

    def test_does_not_attribute_nested_function_generator_to_outer(self):
        src = """
        def outer():
            try:
                def inner():
                    yield 1
            finally:
                cleanup()
        """
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_reports_nested_generator_independently(self):
        src = """
        def outer():
            def inner():
                with open("x") as f:
                    yield f.read()
            yield 1
        """
        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].line == 3

    def test_reports_multiple_cleanup_blocks(self):
        src = """
        def gen():
            try:
                yield 1
            finally:
                cleanup1()

            try:
                yield 2
            finally:
                cleanup2()
        """
        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_yield_after_try_is_clean(self):
        src = """
        def gen():
            try:
                x = 1
            finally:
                cleanup()
            yield 1
        """
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_yield_from_in_try(self):
        src = """
        def gen():
            try:
                yield from source
            finally:
                cleanup()
        """
        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_yield_in_with_inside_loop(self):
        src = """
        def gen():
            for item in items:
                with resource() as r:
                    yield r
        """
        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_async_nested_function_does_not_leak_into_outer(self):
        src = """
        def outer():
            try:
                async def inner():
                    yield 1
            finally:
                cleanup()
        """
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_class_method_generator_is_independent(self):
        src = """
        class Example:
            def outer(self):
                try:
                    def inner():
                        yield 1
                finally:
                    cleanup()
        """
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_lambda_scope_does_not_leak(self):
        src = """
        def outer():
            try:
                fn = lambda: iter(())
            finally:
                cleanup()
            yield 1
        """
        findings = run(self.rule, src)

        assert len(findings) == 0