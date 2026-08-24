import ast
import textwrap

from pyrift.rules.pypy.ppy040_subprocess_pipe import SubprocessPipeRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY040:
    rule = SubprocessPipeRule()

    def test_detects_popen_stdout_pipe(self):
        src = """
import subprocess
p = subprocess.Popen(['ls'], stdout=subprocess.PIPE)
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY040"

    def test_detects_popen_stdin_pipe(self):
        src = """
import subprocess
p = subprocess.Popen(['cat'], stdin=subprocess.PIPE)
"""
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_clean_popen_no_pipe(self):
        src = """
import subprocess
p = subprocess.Popen(['ls'])
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_communicate(self):
        src = "subprocess.Popen(['cmd'], stdout=subprocess.PIPE)"
        findings = run(self.rule, src)
        assert "communicate" in findings[0].suggestion.lower()