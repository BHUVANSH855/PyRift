from pyrift.finding import Finding, Runtime, Severity
from pyrift.fingerprint import finding_fingerprint


def make_finding(
    *,
    line=10,
    col=4,
    title="Example finding",
    description="Example description",
    suggestion="Example suggestion",
    docs_url="https://example.com",
):
    return Finding(
        file="src/example.py",
        line=line,
        col=col,
        rule_id="PPY999",
        title=title,
        description=description,
        severity=Severity.WARNING,
        runtime=Runtime.PYPY,
        affected_from="3.10",
        affected_until="3.13",
        suggestion=suggestion,
        docs_url=docs_url,
    )


class TestFindingFingerprint:
    def test_same_finding_has_same_fingerprint(self):
        first = make_finding()
        second = make_finding()

        assert finding_fingerprint(first) == finding_fingerprint(second)

    def test_line_number_does_not_change_fingerprint(self):
        first = make_finding(line=10)
        second = make_finding(line=100)

        assert finding_fingerprint(first) == finding_fingerprint(second)

    def test_column_number_does_not_change_fingerprint(self):
        first = make_finding(col=4)
        second = make_finding(col=20)

        assert finding_fingerprint(first) == finding_fingerprint(second)

    def test_description_does_not_change_fingerprint(self):
        first = make_finding(description="Original description")
        second = make_finding(description="Updated description")

        assert finding_fingerprint(first) == finding_fingerprint(second)

    def test_suggestion_does_not_change_fingerprint(self):
        first = make_finding(suggestion="Original suggestion")
        second = make_finding(suggestion="Updated suggestion")

        assert finding_fingerprint(first) == finding_fingerprint(second)

    def test_docs_url_does_not_change_fingerprint(self):
        first = make_finding(docs_url="https://example.com/one")
        second = make_finding(docs_url="https://example.com/two")

        assert finding_fingerprint(first) == finding_fingerprint(second)

    def test_rule_id_changes_fingerprint(self):
        first = make_finding()
        second = make_finding()
        second.rule_id = "CPY999"

        assert finding_fingerprint(first) != finding_fingerprint(second)

    def test_runtime_changes_fingerprint(self):
        first = make_finding()
        second = make_finding()
        second.runtime = Runtime.CPYTHON

        assert finding_fingerprint(first) != finding_fingerprint(second)

    def test_version_range_changes_fingerprint(self):
        first = make_finding()
        second = make_finding()
        second.affected_from = "3.11"

        assert finding_fingerprint(first) != finding_fingerprint(second)

    def test_file_changes_fingerprint(self):
        first = make_finding()
        second = make_finding()
        second.file = "src/other.py"

        assert finding_fingerprint(first) != finding_fingerprint(second)

    def test_title_changes_fingerprint(self):
        first = make_finding()
        second = make_finding()
        second.title = "Different finding"

        assert finding_fingerprint(first) != finding_fingerprint(second)

    def test_windows_and_posix_paths_have_same_fingerprint(self):
        first = make_finding()
        first.file = r"src\example.py"

        second = make_finding()
        second.file = "src/example.py"

        assert finding_fingerprint(first) == finding_fingerprint(second)

    def test_fingerprint_is_sha256_hex(self):
        finding = make_finding()

        fingerprint = finding_fingerprint(finding)

        assert len(fingerprint) == 64
        assert all(
            character in "0123456789abcdef"
            for character in fingerprint
        )

    def test_windows_absolute_path_normalized(self):
        # C:\path\to\src\example.py and C:/path/to/src/example.py
        # should have same fingerprint (backslash vs forward slash)
        first = make_finding()
        first.file = r"C:\path\to\src\example.py"

        second = make_finding()
        second.file = "path/to/src/example.py"

        assert finding_fingerprint(first) == finding_fingerprint(second)

    def test_absolute_posix_path_normalized(self):
        # /home/user/project/src.py → src.py (leading slash stripped)
        first = make_finding()
        first.file = "/home/user/project/src/example.py"

        second = make_finding()
        second.file = "src/example.py"

        # Different paths but normalized — different findings
        assert finding_fingerprint(first) != finding_fingerprint(second)

    def test_fingerprint_stable_across_calls(self):
        finding = make_finding()
        fp1 = finding_fingerprint(finding)
        fp2 = finding_fingerprint(finding)
        assert fp1 == fp2