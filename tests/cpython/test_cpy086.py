"""Tests for CPY086 -- os.popen() / os.spawn*() soft-deprecated 3.14."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy086_os_popen_spawn import OsPopenSpawnRule

RULE = OsPopenSpawnRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_os_popen():
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY086"


def test_os_spawnl():
    src = "import os\nos.spawnl(os.P_WAIT, '/bin/ls', 'ls')\n"
    assert len(_findings(src)) == 1


def test_os_spawnle():
    src = "import os\nos.spawnle(os.P_WAIT, '/bin/ls', 'ls', {})\n"
    assert len(_findings(src)) == 1


def test_os_spawnv():
    src = "import os\nos.spawnv(os.P_WAIT, '/bin/ls', ['ls'])\n"
    assert len(_findings(src)) == 1


def test_os_spawnve():
    src = "import os\nos.spawnve(os.P_WAIT, '/bin/ls', ['ls'], {})\n"
    assert len(_findings(src)) == 1


def test_os_spawnvp():
    src = "import os\nos.spawnvp(os.P_WAIT, 'ls', ['ls'])\n"
    assert len(_findings(src)) == 1


def test_popen_in_nested_scope():
    src = (
        "import os\n"
        "def run():\n"
        "    return os.popen('echo hello')\n"
    )
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_subprocess_popen():
    src = "import subprocess\nsubprocess.Popen(['ls'])\n"
    assert _findings(src) == []


def test_os_getcwd():
    src = "import os\nos.getcwd()\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []