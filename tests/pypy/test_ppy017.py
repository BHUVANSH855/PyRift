import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy017_del_existing_class import DelExistingClassRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: DelExistingClassRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY017:
    rule = DelExistingClassRule()

    def test_detects_del_assignment_to_existing_class(self):
        src = """
        class MyClass:
            pass

        MyClass.__del__ = lambda self: None
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY017"
        assert findings[0].severity == Severity.ERROR

    def test_detects_function_assignment_to_existing_class(self):
        src = """
        class MyClass:
            pass

        def cleanup(self):
            pass

        MyClass.__del__ = cleanup
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_detects_assignment_to_lowercase_class_name(self):
        src = """
        class resource:
            pass

        resource.__del__ = cleanup
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_clean_del_in_class_body(self):
        src = """
        class MyClass:
            def __del__(self):
                pass
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_other_class_attribute(self):
        src = """
        class MyClass:
            pass

        MyClass.cleanup = lambda self: None
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_instance_del_assignment(self):
        src = """
        class MyClass:
            pass

        obj = MyClass()
        obj.__del__ = cleanup
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_self_del_assignment(self):
        src = """
        class MyClass:
            def setup(self):
                self.__del__ = cleanup
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_dynamic_receiver(self):
        src = """
        get_class().__del__ = cleanup
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_subscript_receiver(self):
        src = """
        classes["MyClass"].__del__ = cleanup
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_unknown_name(self):
        src = """
        A.__del__ = lambda self: None
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_suggestion_mentions_class_body(self):
        src = """
        class MyClass:
            pass

        MyClass.__del__ = lambda self: None
        """

        findings = run(self.rule, src)

        assert "class" in findings[0].suggestion.lower()