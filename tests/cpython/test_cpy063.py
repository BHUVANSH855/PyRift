import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy063_annotationlib import AnnotationLibRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY063:
    rule = AnnotationLibRule()

    def test_detects_import_annotationlib(self):
        findings = run(self.rule, "import annotationlib")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY063"
        assert findings[0].severity == Severity.ERROR

    def test_detects_from_import(self):
        findings = run(self.rule,
            "from annotationlib import get_annotations, Format")
        assert len(findings) >= 1

    def test_clean_typing_import(self):
        findings = run(self.rule, "import typing")
        assert len(findings) == 0

    def test_suggestion_mentions_get_type_hints(self):
        findings = run(self.rule, "import annotationlib")
        assert "get_type_hints" in findings[0].suggestion