"""Tests for CPY091 -- generator.throw() 3-argument form deprecated 3.12."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy091_generator_throw_args import GeneratorThrowArgsRule

RULE = GeneratorThrowArgsRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_throw_two_args():
    src = "gen.throw(ValueError, 'msg')\n"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY091"


def test_throw_three_args():
    src = "gen.throw(ValueError, exc, tb)\n"
    assert len(_findings(src)) == 1


def test_throw_type_plus_instance():
    src = "gen.throw(TypeError, TypeError('oops'), None)\n"
    assert len(_findings(src)) == 1


def test_coroutine_throw_two_args():
    src = "coro.throw(StopIteration, StopIteration())\n"
    assert len(_findings(src)) == 1


def test_throw_in_loop():
    src = (
        "for gen in generators:\n"
        "    gen.throw(ValueError, 'msg')\n"
    )
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_throw_one_arg():
    src = "gen.throw(ValueError('oops'))\n"
    assert _findings(src) == []


def test_throw_exception_instance():
    src = "exc = ValueError('x')\ngen.throw(exc)\n"
    assert _findings(src) == []


def test_unrelated_throw():
    src = "logger.throw('error')\n"
    # 1 positional arg only → should not fire
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []