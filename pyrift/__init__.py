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
from .scanner  import scan, scan_file, ScanResult, ALL_RULES
from .finding  import Finding, Severity, Runtime
from .reporter import to_json, to_markdown, to_text

__version__ = "0.3.1"
__author__  = "Bhuvansh Kataria"
__license__ = "MIT"

__all__ = [
    "scan",
    "scan_file",
    "ScanResult",
    "ALL_RULES",
    "Finding",
    "Severity",
    "Runtime",
    "to_json",
    "to_markdown",
    "to_text",
    "__version__",
]