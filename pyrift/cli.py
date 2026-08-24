"""
pyrift.cli
~~~~~~~~~~
Command-line interface.

    pyrift scan .
    pyrift scan ./myproject --format json
    pyrift scan ./myproject --format markdown
    pyrift --version
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from . import __version__
from .scanner  import scan
from .reporter import to_text, to_json, to_markdown


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyrift",
        description=(
            "pyrift — detect silent Python behaviour differences "
            "across CPython versions and CPython vs PyPy."
        ),
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"pyrift {__version__}",
    )

    sub = parser.add_subparsers(dest="command")

    scan_cmd = sub.add_parser("scan", help="Scan a file or directory")
    scan_cmd.add_argument(
        "path",
        nargs="?",
        default=".",
        help="File or directory to scan (default: current directory)",
    )
    scan_cmd.add_argument(
        "--format", "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    scan_cmd.add_argument(
        "--output", "-o",
        default=None,
        help="Write output to a file instead of stdout",
    )
    scan_cmd.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit 0 even when findings are found",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "scan":
        path = Path(args.path)
        if not path.exists():
            print(f"pyrift: path not found: {path}", file=sys.stderr)
            sys.exit(2)

        result = scan(path)

        if args.format == "json":
            output = to_json(result)
        elif args.format == "markdown":
            output = to_markdown(result)
        else:
            output = to_text(result)

        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")