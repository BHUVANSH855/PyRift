"""Tests for CPY089 -- platform.java_ver() removed 3.15."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy089_platform_java_ver import PlatformJavaVerRule

RULE = PlatformJavaVerRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_platform_java_ver():
    src = "import platform\nplatform.java_ver()\n"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY089"


def test_platform_java_ver_in_condition():
    src = (
        "import platform\n"
        "if platform.java_ver()[0]:\n"
        "    pass\n"
    )
    assert len(_findings(src)) == 1


def test_module_alias():
    src = "import platform as pl\npl.java_ver()\n"
    assert len(_findings(src)) == 1


def test_platform_java_ver_assigned():
    src = "import platform\nv = platform.java_ver()\n"
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_platform_python_version():
    src = "import platform\nplatform.python_version()\n"
    assert _findings(src) == []


def test_platform_system():
    src = "import platform\nplatform.system()\n"
    assert _findings(src) == []


def test_platform_implementation():
    src = "import platform\nplatform.python_implementation()\n"
    assert _findings(src) == []


def test_unrelated_java_ver():
    src = "java_sdk.java_ver()\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []