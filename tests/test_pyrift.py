"""
pyrift test suite
~~~~~~~~~~~~~~~~~
Run with:  pytest tests/ -v
"""
import ast
import textwrap
import json
import pytest
from pathlib import Path

from pyrift.finding import Severity, Runtime
from pyrift.scanner import scan_file, scan, ScanResult
from pyrift.rules.cpython.cpy001_dict_ordering    import DictOrderingRule
from pyrift.rules.cpython.cpy002_exception_notes  import ExceptionNotesRule
from pyrift.rules.cpython.cpy003_union_type_syntax import UnionTypeSyntaxRule
from pyrift.rules.cpython.cpy004_tomllib          import TomllibRule
from pyrift.rules.cpython.cpy005_match_case       import MatchCaseRule
from pyrift.rules.cpython.cpy006_asyncio_timeout  import AsyncioTimeoutRule
from pyrift.rules.cpython.cpy007_removed_modules  import RemovedModulesRule
from pyrift.rules.cpython.cpy008_slots_dict       import SlotsDictRule
from pyrift.rules.cpython.cpy009_exception_group  import ExceptionGroupRule
from pyrift.rules.cpython.cpy010_dataclass_slots  import DataclassSlotsRule
from pyrift.rules.pypy.ppy001_gc_finalizer        import GcFinalizerRule
from pyrift.rules.pypy.ppy002_ctypes              import CtypesRule
from pyrift.rules.pypy.ppy003_getrefcount         import GetRefcountRule
from pyrift.rules.pypy.ppy004_weakref_proxy       import WeakrefProxyRule
from pyrift.rules.pypy.ppy005_io_buffering        import IoBufferingRule
from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
from pyrift.rules.pypy.ppy007_sys_intern          import SysInternRule
from pyrift.reporter import to_json, to_markdown, to_text


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))

def run_rule(rule, src: str):
    return rule.check(parse(src), "<test>")


# ── CPY001 ────────────────────────────────────────────────────────────────

class TestCPY001:
    rule = DictOrderingRule()

    def test_detects_keys_comparison(self):
        findings = run_rule(self.rule, "d = {'a': 1}; assert d.keys() == ['a']")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY001"
        assert findings[0].severity == Severity.WARNING

    def test_detects_values_comparison(self):
        findings = run_rule(self.rule, "d = {'a': 1}; assert d.values() == [1]")
        assert len(findings) == 1

    def test_clean_code_no_finding(self):
        findings = run_rule(self.rule, "assert set(d.keys()) == {'a'}")
        assert len(findings) == 0

    def test_finding_has_suggestion(self):
        findings = run_rule(self.rule, "d.items() == [('a', 1)]")
        if findings:
            assert findings[0].suggestion != ""


# ── CPY002 ────────────────────────────────────────────────────────────────

class TestCPY002:
    rule = ExceptionNotesRule()

    def test_detects_add_note(self):
        src = """
            try:
                pass
            except ValueError as e:
                e.add_note("extra context")
                raise
        """
        findings = run_rule(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY002"
        assert findings[0].severity == Severity.ERROR

    def test_clean_code_no_finding(self):
        findings = run_rule(self.rule, "e = ValueError('oops')")
        assert len(findings) == 0

    def test_docs_url_present(self):
        findings = run_rule(self.rule, "e.add_note('note')")
        assert findings[0].docs_url != ""


# ── CPY003 ────────────────────────────────────────────────────────────────

class TestCPY003:
    rule = UnionTypeSyntaxRule()

    def test_detects_union_in_isinstance(self):
        findings = run_rule(self.rule, "isinstance(x, int | str)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY003"
        assert findings[0].severity == Severity.ERROR

    def test_clean_isinstance_with_tuple(self):
        findings = run_rule(self.rule, "isinstance(x, (int, str))")
        assert len(findings) == 0


# ── CPY004 ────────────────────────────────────────────────────────────────

class TestCPY004:
    rule = TomllibRule()

    def test_detects_import_tomllib(self):
        findings = run_rule(self.rule, "import tomllib")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY004"
        assert findings[0].severity == Severity.ERROR

    def test_detects_from_import(self):
        findings = run_rule(self.rule, "from tomllib import loads")
        assert len(findings) == 1

    def test_clean_no_tomllib(self):
        findings = run_rule(self.rule, "import json")
        assert len(findings) == 0

    def test_suggestion_mentions_tomli(self):
        findings = run_rule(self.rule, "import tomllib")
        assert "tomli" in findings[0].suggestion.lower()


# ── CPY005 ────────────────────────────────────────────────────────────────

class TestCPY005:
    rule = MatchCaseRule()

    def test_detects_match_statement(self):
        src = """
match command:
    case "quit":
        quit()
    case "go":
        go()
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY005"
        assert findings[0].severity == Severity.ERROR

    def test_clean_if_else(self):
        src = """
if command == "quit":
    quit()
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 0


# ── CPY006 ────────────────────────────────────────────────────────────────

class TestCPY006:
    rule = AsyncioTimeoutRule()

    def test_detects_asyncio_timeout(self):
        findings = run_rule(self.rule, "async with asyncio.timeout(5): pass")
        assert len(findings) >= 1
        assert findings[0].rule_id == "CPY006"

    def test_detects_taskgroup(self):
        findings = run_rule(self.rule, "async with asyncio.TaskGroup() as tg: pass")
        assert len(findings) >= 1

    def test_clean_asyncio_sleep(self):
        findings = run_rule(self.rule, "await asyncio.sleep(1)")
        assert len(findings) == 0


# ── CPY007 ────────────────────────────────────────────────────────────────

class TestCPY007:
    rule = RemovedModulesRule()

    def test_detects_cgi(self):
        findings = run_rule(self.rule, "import cgi")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY007"
        assert findings[0].severity == Severity.ERROR

    def test_detects_asynchat(self):
        findings = run_rule(self.rule, "import asynchat")
        assert len(findings) == 1

    def test_detects_telnetlib(self):
        findings = run_rule(self.rule, "from telnetlib import Telnet")
        assert len(findings) == 1

    def test_clean_standard_module(self):
        findings = run_rule(self.rule, "import os")
        assert len(findings) == 0

    def test_multiple_removed_modules(self):
        src = "import cgi\nimport aifc\nimport uu"
        findings = run_rule(self.rule, src)
        assert len(findings) == 3


# ── CPY008 ────────────────────────────────────────────────────────────────

class TestCPY008:
    rule = SlotsDictRule()

    def test_detects_slots_with_base(self):
        src = """
class Base:
    pass

class Child(Base):
    __slots__ = ['x', 'y']
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY008"
        assert findings[0].severity == Severity.INFO

    def test_clean_slots_no_base(self):
        src = """
class MyClass:
    __slots__ = ['x', 'y']
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 0

    def test_clean_object_base(self):
        src = """
class MyClass(object):
    __slots__ = ['x']
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 0


# ── CPY009 ────────────────────────────────────────────────────────────────

class TestCPY009:
    rule = ExceptionGroupRule()

    def test_detects_exception_group(self):
        findings = run_rule(self.rule, "eg = ExceptionGroup('errors', [e1, e2])")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY009"
        assert findings[0].severity == Severity.ERROR

    def test_detects_base_exception_group(self):
        findings = run_rule(self.rule, "eg = BaseExceptionGroup('errors', [e])")
        assert len(findings) == 1

    def test_clean_regular_exception(self):
        findings = run_rule(self.rule, "raise ValueError('oops')")
        assert len(findings) == 0

    def test_suggestion_mentions_backport(self):
        findings = run_rule(self.rule, "ExceptionGroup('x', [])")
        assert "exceptiongroup" in findings[0].suggestion.lower()


# ── CPY010 ────────────────────────────────────────────────────────────────

class TestCPY010:
    rule = DataclassSlotsRule()

    def test_detects_dataclass_slots(self):
        src = """
from dataclasses import dataclass

@dataclass(slots=True)
class Point:
    x: float
    y: float
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY010"
        assert findings[0].severity == Severity.ERROR

    def test_clean_dataclass_no_slots(self):
        src = """
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 0

    def test_clean_dataclass_slots_false(self):
        src = """
@dataclass(slots=False)
class Point:
    x: float
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_requires_python(self):
        src = """
@dataclass(slots=True)
class X:
    a: int
"""
        findings = run_rule(self.rule, src)
        assert "pyproject" in findings[0].suggestion.lower()


# ── PPY001 ────────────────────────────────────────────────────────────────

class TestPPY001:
    rule = GcFinalizerRule()

    def test_detects_close_in_del(self):
        src = """
            class MyResource:
                def __del__(self):
                    self.file.close()
        """
        findings = run_rule(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY001"
        assert findings[0].runtime == Runtime.PYPY

    def test_detects_flush_in_del(self):
        src = """
            class MyResource:
                def __del__(self):
                    self.conn.flush()
        """
        findings = run_rule(self.rule, src)
        assert len(findings) == 1

    def test_clean_del_no_resource(self):
        src = """
            class MyResource:
                def __del__(self):
                    self.count -= 1
        """
        findings = run_rule(self.rule, src)
        assert len(findings) == 0


# ── PPY002 ────────────────────────────────────────────────────────────────

class TestPPY002:
    rule = CtypesRule()

    def test_detects_ctypes_cdll(self):
        src = "import ctypes\nlib = ctypes.CDLL('libfoo.so')"
        findings = run_rule(self.rule, src)
        assert any(f.rule_id == "PPY002" for f in findings)

    def test_no_finding_without_import(self):
        findings = run_rule(self.rule, "x = CDLL('foo')")
        assert len(findings) == 0

    def test_cffi_suggestion_present(self):
        src = "import ctypes\nctypes.cast(ptr, ctypes.c_void_p)"
        findings = run_rule(self.rule, src)
        if findings:
            assert "cffi" in findings[0].suggestion.lower()


# ── PPY003 ────────────────────────────────────────────────────────────────

class TestPPY003:
    rule = GetRefcountRule()

    def test_detects_getrefcount(self):
        findings = run_rule(self.rule, "import sys\nx = sys.getrefcount(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY003"
        assert findings[0].severity == Severity.ERROR

    def test_clean_sys_version(self):
        findings = run_rule(self.rule, "import sys\nprint(sys.version)")
        assert len(findings) == 0

    def test_suggestion_mentions_gc(self):
        findings = run_rule(self.rule, "sys.getrefcount(x)")
        assert "gc" in findings[0].suggestion.lower()


# ── PPY004 ────────────────────────────────────────────────────────────────

class TestPPY004:
    rule = WeakrefProxyRule()

    def test_detects_weakref_proxy(self):
        src = "import weakref\np = weakref.proxy(obj)"
        findings = run_rule(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY004"
        assert findings[0].severity == Severity.WARNING

    def test_clean_weakref_ref(self):
        src = "import weakref\nr = weakref.ref(obj)"
        findings = run_rule(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_ref(self):
        findings = run_rule(self.rule, "weakref.proxy(obj)")
        assert "ref()" in findings[0].suggestion


# ── PPY005 ────────────────────────────────────────────────────────────────

class TestPPY005:
    rule = IoBufferingRule()

    def test_detects_write_mode_open(self):
        findings = run_rule(self.rule, "f = open('file.txt', 'w')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY005"
        assert findings[0].severity == Severity.WARNING

    def test_detects_append_mode(self):
        findings = run_rule(self.rule, "f = open('log.txt', 'a')")
        assert len(findings) == 1

    def test_clean_read_mode(self):
        findings = run_rule(self.rule, "f = open('file.txt', 'r')")
        assert len(findings) == 0

    def test_suggestion_mentions_context_manager(self):
        findings = run_rule(self.rule, "f = open('file.txt', 'w')")
        assert "with" in findings[0].suggestion.lower()


# ── PPY006 ────────────────────────────────────────────────────────────────

class TestPPY006:
    rule = BuiltinMonkeyPatchRule()

    def test_detects_list_patch(self):
        findings = run_rule(self.rule, "list.custom = lambda self: None")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY006"
        assert findings[0].severity == Severity.WARNING

    def test_detects_dict_patch(self):
        findings = run_rule(self.rule, "dict.merge = lambda self, other: None")
        assert len(findings) == 1

    def test_clean_subclass(self):
        src = """
class MyList(list):
    def custom(self):
        pass
"""
        findings = run_rule(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_subclass(self):
        findings = run_rule(self.rule, "str.shout = lambda self: self.upper()")
        assert "subclass" in findings[0].suggestion.lower()


# ── PPY007 ────────────────────────────────────────────────────────────────

class TestPPY007:
    rule = SysInternRule()

    def test_detects_sys_intern(self):
        findings = run_rule(self.rule, "import sys\ns = sys.intern('hello')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY007"
        assert findings[0].severity == Severity.WARNING

    def test_clean_sys_version(self):
        findings = run_rule(self.rule, "import sys\nprint(sys.version)")
        assert len(findings) == 0

    def test_suggestion_mentions_equality(self):
        findings = run_rule(self.rule, "sys.intern('x')")
        assert "==" in findings[0].suggestion


# ── Scanner ───────────────────────────────────────────────────────────────

class TestScanner:
    def test_scan_file_returns_findings(self, tmp_path):
        f = tmp_path / "sample.py"
        f.write_text("import ctypes\nctypes.CDLL('foo')\n")
        findings = scan_file(f)
        assert isinstance(findings, list)

    def test_scan_directory(self, tmp_path):
        (tmp_path / "a.py").write_text("e.add_note('x')\n")
        (tmp_path / "b.py").write_text("x = 1\n")
        result = scan(tmp_path)
        assert isinstance(result, ScanResult)
        assert result.files_scanned == 2

    def test_score_is_100_for_clean_code(self, tmp_path):
        (tmp_path / "clean.py").write_text("x = 1 + 1\n")
        result = scan(tmp_path)
        assert result.score == 100

    def test_score_decreases_with_errors(self, tmp_path):
        (tmp_path / "bad.py").write_text("e.add_note('x')\n")
        result = scan(tmp_path)
        assert result.score < 100

    def test_skips_venv_dirs(self, tmp_path):
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "noise.py").write_text("e.add_note('x')\n")
        (tmp_path / "real.py").write_text("x = 1\n")
        result = scan(tmp_path)
        assert result.files_scanned == 1

    def test_syntax_error_file_reported(self, tmp_path):
        (tmp_path / "broken.py").write_text("def foo(\n")
        findings = scan_file(tmp_path / "broken.py")
        assert any(f.rule_id == "PARSE" for f in findings)


# ── Reporter ──────────────────────────────────────────────────────────────

class TestReporter:
    def _result(self, tmp_path):
        (tmp_path / "t.py").write_text("e.add_note('x')\n")
        return scan(tmp_path)

    def test_json_is_valid(self, tmp_path):
        data = json.loads(to_json(self._result(tmp_path)))
        assert "summary" in data
        assert "findings" in data

    def test_markdown_contains_header(self, tmp_path):
        assert "# pyrift" in to_markdown(self._result(tmp_path))

    def test_text_output_contains_score(self, tmp_path):
        txt = to_text(self._result(tmp_path))
        assert "Score" in txt or "score" in txt

    def test_clean_result_text(self, tmp_path):
        (tmp_path / "c.py").write_text("x = 1\n")
        result = scan(tmp_path)
        assert "No issues" in to_text(result)