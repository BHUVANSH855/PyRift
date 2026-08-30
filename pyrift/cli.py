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
import inspect
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
from .reporter import to_json, to_markdown, to_sarif, to_text
from .scanner import ALL_RULES, ScanResult, scan
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
        choices=["text", "json", "markdown", "sarif"],
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
        "--new",
        action="store_true",
        dest="new_only",
        help=(
            "PR mode: require a baseline and show only NEW findings "
            "not present in the baseline."
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

    explain_cmd = sub.add_parser(
        "explain",
        help="Explain a rule by its ID (e.g. CPY055)",
    )
    explain_cmd.add_argument(
        "rule_id",
        help="Rule ID to explain (e.g. CPY055)",
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

    if output_format == "sarif":
        return to_sarif(result)

    return to_text(result)

def _scan_changed_files(
    path: Path,
    args: argparse.Namespace,
    target_config: TargetConfig | None,
) -> tuple[ScanResult, int]:
    """Scan only Git-changed Python files."""
    try:
        changed = changed_python_files(path, args.base)
    except GitError as exc:
        print(f"pyrift: {exc}", file=sys.stderr)
        sys.exit(2)

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

    return result, len(changed)


def _apply_baseline(
    result: ScanResult,
    path: Path,
    args: argparse.Namespace,
) -> ScanResult:
    """Apply baseline or --new filtering to a scan result."""
    if getattr(args, "new_only", False):
        baseline_path = Path(DEFAULT_BASELINE_FILE)

        if not baseline_path.exists():
            print(
                f"pyrift: --new requires a baseline file "
                f"({DEFAULT_BASELINE_FILE}). Run "
                f"'pyrift baseline create' first.",
                file=sys.stderr,
            )
            sys.exit(2)

        try:
            baseline = load_baseline(baseline_path)
        except BaselineError as exc:
            print(
                f"pyrift: invalid baseline: {exc}",
                file=sys.stderr,
            )
            sys.exit(2)

        new_findings, baseline_findings = filter_baseline_findings(
            result.findings,
            baseline,
            root=str(path),
        )

        return ScanResult(
            new_findings,
            result.files_scanned,
            baseline_suppressed=len(baseline_findings),
            rule_errors=result.rule_errors,
        )

    if args.no_baseline:
        return result

    baseline_path = Path(DEFAULT_BASELINE_FILE)

    if not baseline_path.exists():
        return result

    try:
        baseline = load_baseline(baseline_path)
    except BaselineError as exc:
        print(
            f"pyrift: invalid baseline: {exc}",
            file=sys.stderr,
        )
        sys.exit(2)

    new_findings, baseline_findings = filter_baseline_findings(
        result.findings,
        baseline,
        root=str(path),
    )

    return ScanResult(
        new_findings,
        result.files_scanned,
        baseline_suppressed=len(baseline_findings),
        rule_errors=result.rule_errors,
    )


def _write_output(
    output: str,
    output_path: str | None,
) -> None:
    """Write formatted output to a file or stdout."""
    if output_path:
        try:
            Path(output_path).write_text(
                output,
                encoding="utf-8",
            )
        except OSError as exc:
            print(
                f"pyrift: unable to write output: {exc}",
                file=sys.stderr,
            )
            sys.exit(2)
    else:
        print(output)


def _run_baseline_create(args: argparse.Namespace) -> None:
    """Handle ``pyrift baseline create``."""
    path = Path(args.path).resolve()

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
            root=str(path),
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


def _run_scan(args: argparse.Namespace) -> None:
    """Handle ``pyrift scan``."""
    path = Path(args.path).resolve()

    if not path.exists():
        print(
            f"pyrift: path not found: {path}",
            file=sys.stderr,
        )
        sys.exit(2)

    target_config = _build_target_config(args)
    changed_count: int | None = None

    if args.changed_only:
        result, changed_count = _scan_changed_files(
            path,
            args,
            target_config,
        )
    else:
        result = scan(
            path,
            target_config=target_config,
            use_project_config=not args.no_project_config,
        )

    result = _apply_baseline(result, path, args)

    output = _format_result(result, args.format)

    if args.changed_only and args.format == "text":
        summary_lines = [
            "PyRift changed-only scan",
            f"Base: {args.base}",
            f"Changed Python files: {changed_count}",
            f"Files scanned: {result.files_scanned}",
            "",
        ]
        output = "\n".join(summary_lines) + output

    _write_output(output, args.output)

    if not args.exit_zero and (result.errors or result.rule_errors):
        sys.exit(1)

    sys.exit(0)


def _run_explain(args: argparse.Namespace) -> None:
    """Handle ``pyrift explain``."""
    rule_id = args.rule_id.upper()

    rule = next(
        (candidate for candidate in ALL_RULES
         if candidate.rule_id == rule_id),
        None,
    )

    if rule is None:
        print(
            f"pyrift: unknown rule ID: {rule_id}",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        from .rule_metadata import RULE_METADATA
    except ImportError:
        RULE_METADATA = {}

    metadata = RULE_METADATA.get(rule_id, {})

    lines = [
        f"Rule:        {rule_id}",
        f"Title:       {rule.title}",
        f"Runtime:     {rule.runtime}",
        f"Category:    {getattr(rule, 'category', 'compatibility')}",
    ]

    confidence = metadata.get("confidence", "low")
    if hasattr(confidence, "value"):
        confidence = confidence.value
    lines.append(f"Confidence:  {confidence}")

    affected_versions = metadata.get("affected_versions", "")
    if affected_versions:
        lines.append(f"Affected:    Python {affected_versions}")

    evidence_type = metadata.get("evidence_type", "")
    if hasattr(evidence_type, "value"):
        evidence_type = evidence_type.value

    evidence_source = metadata.get("evidence_source", "")
    if hasattr(evidence_source, "value"):
        evidence_source = evidence_source.value

    lines.append(
        f"Evidence:    {evidence_type} ({evidence_source})"
    )

    intent_basis = metadata.get("intent_basis", "inferred")
    if hasattr(intent_basis, "value"):
        intent_basis = intent_basis.value
    lines.append(f"Intent basis: {intent_basis}")

    # Extract description and suggestion from the rule's docstring
    doc = inspect.getdoc(rule.__class__) or ""
    if doc:
        # First paragraph after the title line
        lines_doc = [l.strip() for l in doc.split("\n") if l.strip()]
        if len(lines_doc) > 1:
            desc_lines = []
            for dl in lines_doc[1:]:
                if dl.startswith(("---", "Detects:")):
                    break
                desc_lines.append(dl)
            if desc_lines:
                lines.append(f"\nDescription:\n  {' '.join(desc_lines)}")

    last_verified = metadata.get("last_verified", "")
    if last_verified:
        lines.append(f"\nLast verified: {last_verified}")

    print("\n".join(lines))
    sys.exit(0)

def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the appropriate command."""
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
            _run_baseline_create(args)
            return

    if args.command == "scan":
        _run_scan(args)
        return

    if args.command == "explain":
        _run_explain(args)
        return


if __name__ == "__main__":
    main()
