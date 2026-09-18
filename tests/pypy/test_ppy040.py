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

class TestPPY040CorrectedClaimAndFalsePositive:
    """2026-09 audit item #20-ish (spot-check pass): the original
    description falsely attributed subprocess.PIPE deadlocks to "GC
    timing differences" on PyPy. Verified against Python's own
    subprocess docs: the actual cause is fixed-size OS pipe buffers
    filling up -- a universal issue on any implementation, not a PyPy
    difference. Also fixes a real false positive: code that already
    correctly calls .communicate() was still being flagged."""

    rule = SubprocessPipeRule()

    def test_does_not_flag_code_that_already_uses_communicate(self):
        src = """
        import subprocess
        p = subprocess.Popen(['ls'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        """
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_still_flags_raw_read_without_communicate(self):
        src = """
        import subprocess
        p = subprocess.Popen(['ls'], stdout=subprocess.PIPE)
        out = p.stdout.read()
        """
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_description_does_not_blame_gc_timing(self):
        src = "subprocess.Popen(['cmd'], stdout=subprocess.PIPE)"
        findings = run(self.rule, src)
        description = findings[0].description.lower()
        assert "gc timing" not in description
        assert "pipe buffer" in description

    def test_description_notes_it_applies_to_both_runtimes(self):
        src = "subprocess.Popen(['cmd'], stdout=subprocess.PIPE)"
        findings = run(self.rule, src)
        description = findings[0].description.lower()
        assert "cpython and pypy" in description
