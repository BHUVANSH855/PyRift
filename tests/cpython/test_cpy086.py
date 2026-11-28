"""Tests for CPY086 -- os.popen() / os.system() / os.spawn*() soft-deprecated 3.14."""
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


def test_os_system():
    src = "import os\nos.system('ls')\n"
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


# --- Metadata assertions ---

def test_affected_from_is_3_14():
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert f[0].affected_from == "3.14"


def test_affected_until_is_empty():
    # Soft deprecation — no removal version scheduled
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert not f[0].affected_until


def test_severity_is_warning():
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    from pyrift.finding import Severity
    assert f[0].severity == Severity.WARNING


def test_description_mentions_deprecated_version():
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert "3.14" in f[0].description


def test_description_names_function():
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert "os.popen" in f[0].description


def test_description_names_system():
    src = "import os\nos.system('ls')\n"
    f = _findings(src)
    assert "os.system" in f[0].description


def test_suggestion_mentions_subprocess():
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert "subprocess" in f[0].suggestion


def test_docs_url_points_to_subprocess():
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert "subprocess" in f[0].docs_url


def test_rule_id_is_cpy086():
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert f[0].rule_id == "CPY086"


def test_affected_until_is_exactly_empty_string():
    # Soft deprecation — no removal scheduled; must be "" not just falsy
    src = "import os\nos.popen('ls')\n"
    f = _findings(src)
    assert f[0].affected_until == "", (
        f"Soft deprecated; no removal date; expected '', got {f[0].affected_until!r}"
    )


# --- Remaining spawn variants ---

def test_os_spawnlp():
    src = "import os\nos.spawnlp(os.P_NOWAIT, 'ls', 'ls')\n"
    assert len(_findings(src)) == 1


def test_os_spawnlpe():
    src = "import os\nos.spawnlpe(os.P_NOWAIT, 'ls', 'ls', {})\n"
    assert len(_findings(src)) == 1


def test_os_spawnvpe():
    src = "import os\nos.spawnvpe(os.P_WAIT, 'ls', ['ls'], {})\n"
    assert len(_findings(src)) == 1


# --- Multiple calls produce multiple findings ---

def test_popen_and_system_two_findings():
    src = "import os\nos.popen('ls')\nos.system('echo hi')\n"
    f = _findings(src)
    assert len(f) == 2


def test_all_spawn_findings_are_warning():
    src = (
        "import os\n"
        "os.spawnl(os.P_WAIT, '/bin/ls', 'ls')\n"
        "os.spawnv(os.P_WAIT, '/bin/ls', ['ls'])\n"
    )
    from pyrift.finding import Severity
    findings = _findings(src)
    assert len(findings) == 2
    assert all(fi.severity == Severity.WARNING for fi in findings)


# --- Negative: unrelated os functions ---

def test_os_path_join_not_flagged():
    src = "import os\nos.path.join('a', 'b')\n"
    assert _findings(src) == []


def test_os_listdir_not_flagged():
    src = "import os\nos.listdir('.')\n"
    assert _findings(src) == []