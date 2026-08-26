import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy007_removed_modules import RemovedModulesRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY007:
    rule = RemovedModulesRule()

    def test_detects_cgi(self):
        findings = run(self.rule, "import cgi")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY007"
        assert findings[0].severity == Severity.ERROR

    def test_detects_asynchat(self):
        findings = run(self.rule, "import asynchat")
        assert len(findings) == 1

    def test_detects_telnetlib(self):
        findings = run(self.rule, "from telnetlib import Telnet")
        assert len(findings) == 1

    def test_clean_standard_module(self):
        findings = run(self.rule, "import os")
        assert len(findings) == 0

    def test_multiple_removed_modules(self):
        findings = run(self.rule, "import cgi\nimport aifc\nimport uu")
        assert len(findings) == 3
    def test_detects_importlib_dynamic(self):
        findings = run(self.rule, "importlib.import_module('cgi')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY007"

    def test_detects_dunder_import(self):
        findings = run(self.rule, "__import__('telnetlib')")
        assert len(findings) == 1

    def test_clean_dynamic_import_non_literal(self):
        # Can't detect dynamic imports with non-literal module names
        findings = run(self.rule, "importlib.import_module(module_name)")
        assert len(findings) == 0

    def test_clean_dynamic_import_not_removed(self):
        findings = run(self.rule, "importlib.import_module('json')")
        assert len(findings) == 0