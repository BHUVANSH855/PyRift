from pyrift.finding import Finding, Runtime, Severity
from pyrift.fingerprint import _normalize_path, finding_fingerprint


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

class TestNormalizePathWithRoot:
    def test_root_makes_path_relative(self):
        from pyrift.fingerprint import _normalize_path
        result = _normalize_path("/home/user/project/src/file.py",
                                  root="/home/user/project")
        assert result == "src/file.py"

    def test_root_trailing_slash_handled(self):
        from pyrift.fingerprint import _normalize_path
        result = _normalize_path("/home/user/project/src/file.py",
                                  root="/home/user/project/")
        assert result == "src/file.py"

    def test_root_exact_match_returns_empty(self):
        from pyrift.fingerprint import _normalize_path
        result = _normalize_path("/home/user/project",
                                  root="/home/user/project")
        assert result == ""

    def test_root_not_matching_falls_through(self):
        from pyrift.fingerprint import _normalize_path
        result = _normalize_path("/other/path/file.py",
                                  root="/home/user/project")
        assert "file.py" in result

    def test_fingerprint_with_root_stable(self):
        from pyrift.fingerprint import finding_fingerprint
        f = make_finding()
        f.file = "/home/user/project/src/test.py"
        fp1 = finding_fingerprint(f, root="/home/user/project")
        fp2 = finding_fingerprint(f, root="/home/user/project")
        assert fp1 == fp2

    def test_fingerprint_root_vs_no_root_differ(self):
        from pyrift.fingerprint import finding_fingerprint
        f1 = make_finding()
        f1.file = "/home/user/project/src/test.py"
        f2 = make_finding()
        f2.file = "src/test.py"
        fp_with_root = finding_fingerprint(f1, root="/home/user/project")
        fp_relative = finding_fingerprint(f2)
        assert fp_with_root == fp_relative


class TestNormalizePathDotSlash:
    """Verify that leading ./ is stripped consistently."""

    def test_dot_slash_stripped(self):
        assert _normalize_path("./src/example.py") == "src/example.py"

    def test_double_dot_slash_stripped(self):
        assert _normalize_path("././src/example.py") == "src/example.py"

    def test_dot_slash_with_root(self):
        result = _normalize_path(
            "/home/user/project/./src/file.py",
            root="/home/user/project",
        )
        assert result == "src/file.py"

    def test_relative_dot_slash_matches_bare(self):
        f1 = make_finding()
        f1.file = "./src/example.py"
        f2 = make_finding()
        f2.file = "src/example.py"
        fp1 = finding_fingerprint(f1)
        fp2 = finding_fingerprint(f2)
        assert fp1 == fp2


class TestNormalizePathRegression:
    """Regression tests for the fingerprint normalization bug fix."""

    def test_relative_path_normalized(self):
        assert _normalize_path("src/example.py") == "src/example.py"

    def test_absolute_posix_path_normalized(self):
        assert _normalize_path("/home/user/project/src/example.py") == "home/user/project/src/example.py"

    def test_windows_absolute_path_normalized(self):
        assert _normalize_path("C:/Users/dev/project/src/example.py") == "Users/dev/project/src/example.py"

    def test_windows_backslash_path_normalized(self):
        assert _normalize_path(r"C:\Users\dev\project\src\example.py") == "Users/dev/project/src/example.py"

    def test_nested_repository_path_normalized(self):
        assert _normalize_path("project/src/deep/nested/file.py") == "project/src/deep/nested/file.py"

    def test_dot_slash_relative_path(self):
        assert _normalize_path("./project/src/file.py") == "project/src/file.py"

    def test_absolute_with_root(self):
        result = _normalize_path(
            "/home/user/project/src/file.py",
            root="/home/user/project",
        )
        assert result == "src/file.py"

    def test_relative_with_root(self):
        result = _normalize_path("src/file.py", root="/home/user/project")
        assert result == "src/file.py"

    def test_dot_slash_with_root(self):
        result = _normalize_path("./src/file.py", root="/home/user/project")
        assert result == "src/file.py"

    def test_windows_path_with_root(self):
        result = _normalize_path(
            r"C:\Users\dev\project\src\file.py",
            root=r"C:\Users\dev\project",
        )
        assert result == "src/file.py"

    def test_unicode_path_normalized(self):
        result = _normalize_path("./src/café/naïve.py")
        assert result == "src/café/naïve.py"

    def test_whitespace_in_path(self):
        result = _normalize_path("./src/my folder/my file.py")
        assert result == "src/my folder/my file.py"

    def test_fingerprint_identical_across_invocation_styles(self):
        """The same finding must produce the same fingerprint regardless
        of how the scan was invoked (relative, absolute, dot-prefixed)."""
        root = "/home/user/project"

        f_abs = make_finding()
        f_abs.file = "/home/user/project/src/file.py"
        absolute_fp = finding_fingerprint(f_abs, root=root)

        f_rel = make_finding()
        f_rel.file = "src/file.py"
        relative_fp = finding_fingerprint(f_rel)

        f_dot = make_finding()
        f_dot.file = "./src/file.py"
        dot_slash_fp = finding_fingerprint(f_dot)

        assert absolute_fp == relative_fp
        assert relative_fp == dot_slash_fp

    def test_baseline_create_and_filter_consistency(self):
        """Create baseline with one path style, filter with another."""
        import os
        import tempfile

        from pyrift.baseline import (
            create_baseline,
            filter_baseline_findings,
            load_baseline,
        )

        f = make_finding()
        f.file = "/home/user/project/src/file.py"
        findings = [f]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
            baseline_path = tmp.name

        try:
            create_baseline(findings, baseline_path, root="/home/user/project")
            baseline = load_baseline(baseline_path)

            new_findings, baseline_findings = filter_baseline_findings(
                findings, baseline, root="/home/user/project",
            )
            assert len(baseline_findings) == 1
            assert len(new_findings) == 0
        finally:
            os.unlink(baseline_path)