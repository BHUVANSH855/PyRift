"""Phase 15: Deterministic output tests."""
from __future__ import annotations

import json
from pathlib import Path

from pyrift import scan, to_json
from pyrift.scanner import _python_files

PYRIFT_SRC = Path(__file__).resolve().parent.parent / "pyrift"


def _scan_twice() -> tuple[list[dict], list[dict]]:
    """Scan the pyrift source directory twice and return JSON dicts."""
    result1 = scan(PYRIFT_SRC, use_project_config=False)
    result2 = scan(PYRIFT_SRC, use_project_config=False)

    json1 = json.loads(to_json(result1))
    json2 = json.loads(to_json(result2))
    return json1, json2


class TestDeterministicOutput:
    """Scanning the same directory twice must produce identical results."""

    def test_findings_count_identical(self) -> None:
        result1 = scan(PYRIFT_SRC, use_project_config=False)
        result2 = scan(PYRIFT_SRC, use_project_config=False)
        c1 = [f for f in result1.findings if f.rule_id != "PARSE"]
        c2 = [f for f in result2.findings if f.rule_id != "PARSE"]
        assert len(c1) == len(c2)

    def test_findings_content_identical(self) -> None:
        result1 = scan(PYRIFT_SRC, use_project_config=False)
        result2 = scan(PYRIFT_SRC, use_project_config=False)

        f1 = [f for f in result1.findings if f.rule_id != "PARSE"]
        f2 = [f for f in result2.findings if f.rule_id != "PARSE"]

        for f1_item, f2_item in zip(f1, f2, strict=True):
            assert f1_item.file == f2_item.file
            assert f1_item.line == f2_item.line
            assert f1_item.rule_id == f2_item.rule_id
            assert f1_item.title == f2_item.title

    def test_findings_ordering_identical(self) -> None:
        result1 = scan(PYRIFT_SRC, use_project_config=False)
        result2 = scan(PYRIFT_SRC, use_project_config=False)

        ids1 = [f.rule_id for f in result1.findings if f.rule_id != "PARSE"]
        ids2 = [f.rule_id for f in result2.findings if f.rule_id != "PARSE"]
        assert ids1 == ids2

    def test_json_output_identical(self) -> None:
        json1, json2 = _scan_twice()
        f1 = [f for f in json1.get("findings", []) if f.get("rule_id") != "PARSE"]
        f2 = [f for f in json2.get("findings", []) if f.get("rule_id") != "PARSE"]
        assert f1 == f2

    def test_file_list_deterministic(self) -> None:
        files1 = list(_python_files(PYRIFT_SRC))
        files2 = list(_python_files(PYRIFT_SRC))
        assert files1 == files2

    def test_files_scanned_count_identical(self) -> None:
        result1 = scan(PYRIFT_SRC, use_project_config=False)
        result2 = scan(PYRIFT_SRC, use_project_config=False)
        assert result1.files_scanned == result2.files_scanned
