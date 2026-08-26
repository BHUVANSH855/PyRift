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

    def test_detects_dict_iteration(self):
        findings = run(
            self.rule,
            "for k in obj.__dict__: pass",
        )

        assert len(findings) == 1

    def test_detects_list_conversion(self):
        findings = run(
            self.rule,
            "keys = list(obj.__dict__)",
        )

        assert len(findings) == 1

    def test_self_dict_inside_method_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            class A:
                def f(self):
                    return list(self.__dict__)
            """,
        )

        assert len(findings) == 0

    def test_suggestion_mentions_order(self):
        findings = run(
            self.rule,
            "for k in obj.__dict__: pass",
        )

        assert "order" in findings[0].suggestion.lower()