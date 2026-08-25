import ast

from pyrift.rules.pypy.ppy031_integer_identity import IntegerIdentityRule


def _findings(source: str):
    tree = ast.parse(source)
    return IntegerIdentityRule().check(tree, "test.py")


def test_detects_integer_literal_identity():
    findings = _findings("x is 1000")

    assert len(findings) == 1
    assert findings[0].rule_id == "PPY031"


def test_detects_integer_expression_identity():
    findings = _findings("x is 1 + 2")

    assert len(findings) == 1
    assert findings[0].rule_id == "PPY031"


def test_detects_integer_literal_is_not():
    findings = _findings("x is not 1000")

    assert len(findings) == 1
    assert findings[0].rule_id == "PPY031"


def test_ignores_none_identity():
    findings = _findings("x is None")

    assert findings == []


def test_ignores_not_none_identity():
    findings = _findings("x is not None")

    assert findings == []


def test_ignores_true_identity():
    findings = _findings("x is True")

    assert findings == []


def test_ignores_false_identity():
    findings = _findings("x is False")

    assert findings == []


def test_ignores_arbitrary_object_identity():
    findings = _findings("x is y")

    assert findings == []


def test_ignores_string_identity():
    findings = _findings("x is 'hello'")

    assert findings == []


def test_ignores_float_identity():
    findings = _findings("x is 1.5")

    assert findings == []


def test_detects_negative_integer_expression():
    findings = _findings("x is -1000")

    assert len(findings) == 1
    assert findings[0].rule_id == "PPY031"