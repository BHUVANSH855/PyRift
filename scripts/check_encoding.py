#!/usr/bin/env python3
"""
Phase 16: BOM/Encoding Quality Gate.

Walk the repository and check all text files for UTF-8 BOM (EF BB BF).
Reports files with BOMs (which are generally unwanted).
Exits 0 if clean, 1 if BOMs found.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "node_modules", "dist", "build",
    ".tox", ".eggs", ".mypy_cache", ".pytest_cache", ".ruff_cache",
}

EXTENSIONS = {".py", ".md", ".json", ".yaml", ".yml", ".toml"}

BOM = b"\xef\xbb\xbf"


def find_bom_files(root: Path) -> list[Path]:
    """Walk the tree and return files that start with a UTF-8 BOM."""
    bom_files: list[Path] = []

    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS
        ]

        for fname in filenames:
            fpath = Path(dirpath) / fname

            if fpath.suffix not in EXTENSIONS:
                continue

            try:
                with open(fpath, "rb") as f:
                    if f.read(3) == BOM:
                        bom_files.append(fpath.relative_to(root))
            except OSError:
                pass

    return sorted(bom_files)


def main() -> int:
    bom_files = find_bom_files(ROOT)

    if bom_files:
        print(f"[FAIL] {len(bom_files)} file(s) contain UTF-8 BOM:")
        for f in bom_files:
            print(f"  {f}")
        return 1

    print("[OK] No UTF-8 BOM found in repository text files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
