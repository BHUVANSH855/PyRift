"""
pyrift.cli
~~~~~~~~~~
Command-line interface.

    pyrift scan .
    pyrift scan ./myproject --format json
    pyrift scan ./myproject --format markdown
    pyrift baseline create
    pyrift baseline create ./myproject
    pyrift --version
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .baseline import (
    DEFAULT_BASELINE_FILE,
    BaselineError,
    create_baseline,
    filter_baseline_findings,
    load_baseline,
)
from .git import GitError, changed_python_files
from .reporter import to_json, to_markdown, to_text
from .scanner import ScanResult, scan
from .targets import PythonVersion, TargetConfig


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyrift",
        description=(
            "pyrift — detect silent Python behaviour differences "
            "across CPython versions and CPython vs PyPy."
        ),
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"pyrift {__version__}",
    )

    sub = parser.add_subparsers(dest="command")

    scan_cmd = sub.add_parser(
        "scan",
        help="Scan a file or directory",
    )
    scan_cmd.add_argument(
        "path",
        nargs="?",
        default=".",
        help="File or directory to scan (default: current directory)",
    )
    scan_cmd.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    scan_cmd.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to a file instead of stdout",
    )
    scan_cmd.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit 0 even when findings are found",
    )
    scan_cmd.add_argument(
        "--python-min",
        default=None,
        help=(
            "Minimum supported CPython version, for example 3.10. "
            "Overrides project.requires-python."
        ),
    )
    scan_cmd.add_argument(
        "--python-max",
        default=None,
        help=(
            "Maximum supported CPython version, for example 3.13. "
            "Overrides project.requires-python."
        ),
    )
    scan_cmd.add_argument(
        "--platform",
        choices=["windows", "linux", "macos", "posix"],
        default=None,
        help=(
            "Target platform for compatibility analysis. "
            "Use 'windows', 'linux', 'macos', or 'posix'."
        ),
    )
    scan_cmd.add_argument(
        "--no-project-config",
        action="store_true",
        help=(
            "Ignore project.requires-python from pyproject.toml."
        ),
    )
    scan_cmd.add_argument(
        "--no-baseline",
        action="store_true",
        help=(
            "Ignore .pyrift-baseline.json when scanning."
        ),
    )
    scan_cmd.add_argument(
        "--changed-only",
        action="store_true",
        help=(
            "Scan only Python files changed relative to the Git base "
            "revision."
        ),
    )

    scan_cmd.add_argument(
        "--base",
        default="HEAD",
        help=(
            "Git revision used as the comparison base for "
            "--changed-only (default: HEAD)."
        ),
    )

    baseline_cmd = sub.add_parser(
        "baseline",
        help="Manage the compatibility finding baseline",
    )

    baseline_sub = baseline_cmd.add_subparsers(
        dest="baseline_command",
    )

    baseline_create_cmd = baseline_sub.add_parser(
        "create",
        help="Create a baseline from the current scan",
    )
    baseline_create_cmd.add_argument(
        "path",
        nargs="?",
        default=".",
        help="File or directory to scan (default: current directory)",
    )
    baseline_create_cmd.add_argument(
        "--output",
        "-o",
        default=DEFAULT_BASELINE_FILE,
        help=(
            "Baseline file to create "
            f"(default: {DEFAULT_BASELINE_FILE})"
        ),
    )
    baseline_create_cmd.add_argument(
        "--python-min",
        default=None,
        help=(
            "Minimum supported CPython version, for example 3.10. "
            "Overrides project.requires-python."
        ),
    )
    baseline_create_cmd.add_argument(
        "--python-max",
        default=None,
        help=(
            "Maximum supported CPython version, for example 3.13. "
            "Overrides project.requires-python."
        ),
    )
    baseline_create_cmd.add_argument(
        "--no-project-config",
        action="store_true",
        help=(
            "Ignore project.requires-python from pyproject.toml."
        ),
    )

    return parser


def _build_target_config(
    args: argparse.Namespace,
) -> TargetConfig | None:
    """Build and validate an optional Python target configuration."""
    if (
        args.python_min is None
        and args.python_max is None
        and getattr(args, "platform", None) is None
    ):
        return None

    try:
        target_config = TargetConfig(
            minimum=(
                PythonVersion.parse(args.python_min)
                if args.python_min is not None
                else None
            ),
            maximum=(
                PythonVersion.parse(args.python_max)
                if args.python_max is not None
                else None
            ),
            platform=getattr(args, "platform", None),
        )
    except ValueError as exc:
        print(
            f"pyrift: invalid Python version: {exc}",
            file=sys.stderr,
        )
        sys.exit(2)

    if (
        target_config.minimum is not None
        and target_config.maximum is not None
        and target_config.minimum > target_config.maximum
    ):
        print(
            "pyrift: --python-min cannot be greater than "
            "--python-max",
            file=sys.stderr,
        )
        sys.exit(2)

    return target_config


def _format_result(
    result: ScanResult,
    output_format: str,
) -> str:
    """Format a scan result using the requested output format."""
    if output_format == "json":
        return to_json(result)

    if output_format == "markdown":
        return to_markdown(result)

    return to_text(result)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "baseline":
        if args.baseline_command is None:
            parser.print_help()
            sys.exit(0)

        if args.baseline_command == "create":
            path = Path(args.path)

            if not path.exists():
                print(
                    f"pyrift: path not found: {path}",
                    file=sys.stderr,
                )
                sys.exit(2)

            target_config = _build_target_config(args)

            result = scan(
                path,
                target_config=target_config,
                use_project_config=not args.no_project_config,
            )

            try:
                create_baseline(
                    result.findings,
                    args.output,
                )
            except OSError as exc:
                print(
                    f"pyrift: unable to create baseline: {exc}",
                    file=sys.stderr,
                )
                sys.exit(2)

            print(
                f"Created baseline with {len(result.findings)} "
                f"finding(s): {args.output}"
            )
            sys.exit(0)

    if args.command == "scan":
        path = Path(args.path)

        if not path.exists():
            print(
                f"pyrift: path not found: {path}",
                file=sys.stderr,
            )
            sys.exit(2)

        target_config = _build_target_config(args)
        changed_count: int | None = None

        if args.changed_only:
            try:
                changed = changed_python_files(path, args.base)
            except GitError as exc:
                print(f"pyrift: {exc}", file=sys.stderr)
                sys.exit(2)

            changed_count = len(changed)

            findings = []
            rule_errors = []
            files_scanned = 0

            for changed_file in changed:
                file_result = scan(
                    changed_file,
                    target_config=target_config,
                    use_project_config=not args.no_project_config,
                )
                findings.extend(file_result.findings)
                rule_errors.extend(file_result.rule_errors)
                files_scanned += file_result.files_scanned

            result = ScanResult(
                findings,
                files_scanned,
                rule_errors=rule_errors,
            )
        else:
            result = scan(
                path,
                target_config=target_config,
                use_project_config=not args.no_project_config,
            )

        if not args.no_baseline:
            baseline_path = Path(DEFAULT_BASELINE_FILE)

            if baseline_path.exists():
                try:
                    baseline = load_baseline(baseline_path)
                except BaselineError as exc:
                    print(
                        f"pyrift: invalid baseline: {exc}",
                        file=sys.stderr,
                    )
                    sys.exit(2)

                new_findings, baseline_findings = (
                    filter_baseline_findings(
                        result.findings,
                        baseline,
                    )
                )

                result = ScanResult(
                    new_findings,
                    result.files_scanned,
                    baseline_suppressed=len(baseline_findings),
                    rule_errors=result.rule_errors,
                )

        output = _format_result(
            result,
            args.format,
        )

        if args.changed_only and args.format == "text":
            summary_lines = [
                "PyRift changed-only scan",
                f"Base: {args.base}",
                f"Changed Python files: {changed_count}",
                f"Files scanned: {result.files_scanned}",
                "",
            ]
            output = "\n".join(summary_lines) + output

        if args.output:
            Path(args.output).write_text(
                output,
                encoding="utf-8",
            )
        else:
            print(output)

        if not args.exit_zero and (result.errors or result.rule_errors):
            sys.exit(1)

        sys.exit(0)


if __name__ == "__main__":
    main()
