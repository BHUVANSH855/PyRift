import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy035_c_extensions import CExtensionsRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY035:
    rule = CExtensionsRule()

    def test_detects_numpy(self):
        findings = run(self.rule, "import numpy")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY035"
        # 2026-09 audit item #16: downgraded from WARNING/HIGH to
        # INFO/MEDIUM -- the original blanket "may crash / produce
        # wrong results" framing overstated risk uniformly across the
        # whole package list; this is a "worth checking" heuristic, not
        # an assumed-broken finding.
        assert findings[0].severity == Severity.INFO

    def test_detects_pandas(self):
        findings = run(self.rule, "import pandas as pd")
        assert len(findings) == 1

    def test_detects_from_import(self):
        findings = run(self.rule, "from scipy import stats")
        assert len(findings) == 1

    def test_clean_pure_python_package(self):
        findings = run(self.rule, "import requests")
        assert len(findings) == 0

    def test_detects_ujson(self):
        findings = run(self.rule, "import ujson")
        assert len(findings) == 1

    def test_detects_hiredis(self):
        findings = run(self.rule, "import hiredis")
        assert len(findings) == 1

    def test_detects_grpcio(self):
        findings = run(self.rule, "import grpc")
        assert len(findings) == 1

    def test_suggestion_mentions_checking_current_support(self):
        findings = run(self.rule, "import numpy")
        suggestion = findings[0].suggestion.lower()
        assert "pypy" in suggestion and "support" in suggestion

    def test_description_does_not_overstate_uniform_breakage(self):
        """2026-09 audit item #16 regression: the description must not
        assert that packages generically crash/produce wrong results on
        PyPy -- current evidence (PyPy's own FAQ: cpyext is "mature
        enough" that numpy "passes the test suite") doesn't support that
        blanket claim."""
        findings = run(self.rule, "import numpy")
        description = findings[0].description.lower()
        assert "produce wrong results" not in description
        assert "verify" in description or "vary" in description

    def test_finding_confidence_is_medium_not_high(self):
        from pyrift.finding import Confidence
        findings = run(self.rule, "import numpy")
        assert findings[0].confidence == Confidence.MEDIUM