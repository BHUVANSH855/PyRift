"""
pyrift
~~~~~~
Detect silent Python behaviour differences across CPython versions
and between CPython and PyPy.

Quick start::

    import pyrift

    result = pyrift.scan("./myproject")
    print(result)
    # ScanResult(files=12, errors=1, warnings=3, score=83)

    for finding in result.findings:
        print(finding)

"""
from .finding import Finding, Runtime, Severity
from .reporter import to_json, to_markdown, to_text
from .scanner import ALL_RULES, ScanResult, scan, scan_file
from .targets import PythonVersion, TargetConfig

__version__ = "0.8.0"
__author__  = "Bhuvansh Kataria"
__license__ = "MIT"

__all__ = [
    "ALL_RULES",
    "Finding",
    "PythonVersion",
    "Runtime",
    "ScanResult",
    "Severity",
    "TargetConfig",
    "__version__",
    "scan",
    "scan_file",
    "to_json",
    "to_markdown",
    "to_text",
]