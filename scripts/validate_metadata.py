"""CI-checkable script: validates rule metadata completeness.

Exits 0 if all metadata entries have required fields, 1 otherwise.
"""
from __future__ import annotations

import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from pyrift.rule_metadata import validate_metadata


def main() -> int:
    if validate_metadata():
        print("Metadata validation passed.")
        return 0
    print("Metadata validation FAILED: missing required fields.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
