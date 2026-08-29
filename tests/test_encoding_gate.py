"""Phase 16: Verify the BOM/encoding gate script runs clean."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_encoding.py"


class TestEncodingGate:
    """The encoding gate must pass on the repository itself."""

    def test_check_encoding_runs_clean(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=SCRIPT.parent.parent,
        )
        assert result.returncode == 0, (
            f"check_encoding.py failed:\n{result.stdout}\n{result.stderr}"
        )
