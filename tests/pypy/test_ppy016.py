import ast
import textwrap

from pyrift.rules.pypy.ppy016_instance_dict_order import (
    InstanceDictOrderRule,
)


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: InstanceDictOrderRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY016:
    rule = InstanceDictOrderRule()

    def test_plain_access_is_not_enough(self):
        findings = run(
            self.rule,
            "x = obj.__dict__",
        )

        assert len(findings) == 0

    def test_plain_subscript_access_is_not_order_sensitive(self):
        findings = run(
            self.rule,
            'x = obj.__dict__["name"]',
        )

        assert len(findings) == 0

    def test_detects_dict_iteration(self):
        findings = run(
            self.rule,
            "for k in obj.__dict__: pass",
        )

        assert len(findings) == 1

    def test_detects_comprehension_iteration(self):
        findings = run(
            self.rule,
            "[key for key in obj.__dict__]",
        )

        assert len(findings) == 1

    def test_detects_list_conversion(self):
        findings = run(
            self.rule,
            "keys = list(obj.__dict__)",
        )

        assert len(findings) == 1

    def test_detects_tuple_conversion(self):
        findings = run(
            self.rule,
            "keys = tuple(obj.__dict__)",
        )

        assert len(findings) == 1

    def test_detects_iter_conversion(self):
        findings = run(
            self.rule,
            "keys = iter(obj.__dict__)",
        )

        assert len(findings) == 1

    def test_sorted_conversion_is_not_order_sensitive(self):
        findings = run(
            self.rule,
            "keys = sorted(obj.__dict__)",
        )

        assert findings == []

    def test_detects_reversed_conversion(self):
        findings = run(
            self.rule,
            "keys = reversed(obj.__dict__)",
        )

        assert len(findings) == 1

    def test_detects_dict_conversion(self):
        findings = run(
            self.rule,
            "data = dict(obj.__dict__)",
        )

        assert len(findings) == 1

    def test_detects_dict_keys(self):
        findings = run(
            self.rule,
            "keys = obj.__dict__.keys()",
        )

        assert len(findings) == 1

    def test_detects_dict_values(self):
        findings = run(
            self.rule,
            "values = obj.__dict__.values()",
        )

        assert len(findings) == 1

    def test_detects_dict_items(self):
        findings = run(
            self.rule,
            "items = obj.__dict__.items()",
        )

        assert len(findings) == 1

    def test_sorted_items_conversion_is_not_order_sensitive(self):
        findings = run(
            self.rule,
            "items = sorted(obj.__dict__.items())",
        )

        assert findings == []

    def test_self_dict_order_sensitive_access_is_flagged(self):
        findings = run(
            self.rule,
            """
            class A:
                def f(self):
                    return list(self.__dict__)
            """,
        )

        assert len(findings) == 1

    def test_self_dict_iteration_is_flagged(self):
        findings = run(
            self.rule,
            """
            class A:
                def f(self):
                    for key in self.__dict__:
                        print(key)
            """,
        )

        assert len(findings) == 1

    def test_self_dict_plain_access_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            class A:
                def f(self):
                    return self.__dict__
            """,
        )

        assert len(findings) == 0

    def test_self_dict_subscript_access_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            class A:
                def f(self):
                    return self.__dict__["name"]
            """,
        )

        assert len(findings) == 0

    def test_suggestion_mentions_order(self):
        findings = run(
            self.rule,
            "list(obj.__dict__)",
        )

        assert "order" in findings[0].suggestion.lower()

    def test_plain_access_with_no_parent_is_not_flagged(self):
        findings = run(
            self.rule,
            "obj.__dict__",
        )

        assert findings == []

    def test_custom_method_on_dict_is_not_order_sensitive(self):
        findings = run(
            self.rule,
            "obj.__dict__.custom_method()",
        )

        assert findings == []

    def test_plain_call_with_object_func_is_not_order_sensitive(self):
        findings = run(
            self.rule,
            "result = factory(obj.__dict__)",
        )

        assert findings == []