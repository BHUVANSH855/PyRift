"""PPY035 -- C extension packages may need PyPy compatibility verification.

2026-09 audit item #16: this rule's original wording ("may not work
correctly... some crash, some produce wrong results") overstated the
risk uniformly across the whole KNOWN_PROBLEMATIC list. Verified against
current evidence (Sept 2026): PyPy's own FAQ states cpyext is "mature
enough" that upstream numpy "passes the test suite" -- the documented
cost for cpyext-based packages is primarily *performance* overhead, not
general correctness breakage -- and several packages in this list
(cryptography, MarkupSafe, pydantic-core) now publish official PyPy
wheels on PyPI, meaning they have first-class native support rather
than running through the cpyext compatibility shim at all.

The rule still flags a real, worth-checking category (per-package,
per-version PyPy support varies and does need verification before
deploying), but presents it as that -- a checklist item -- rather than
an assumed-broken warning. A future PPY-CAPI-001-style rule that
inspects actual C-API usage patterns (rather than the mere presence of
an import) would be the real fix for the underlying precision problem;
this change only corrects the current rule's overstated framing.
"""
from __future__ import annotations

import ast

from pyrift.analysis.imports import collect_imports
from pyrift.base_rule import BaseRule
from pyrift.finding import Confidence, Finding, Runtime, Severity
from pyrift.targets import TargetConfig

KNOWN_PROBLEMATIC = {
    "numpy", "pandas", "scipy", "torch", "tensorflow",
    "psycopg2", "lxml", "Pillow", "PIL", "cv2",
    "sklearn", "matplotlib", "cryptography",
    "h5py", "pyyaml", "ujson", "orjson", "msgpack",
    "pycurl", "pyzmq", "grpcio", "protobuf",
    "hiredis", "regex", "xxhash", "blake3",
    "greenlet", "gevent", "eventlet", "bcrypt",
    "pydantic", "mypy_extensions", "Cython",
    "pybind11", "MarkupSafe", "grpc",
}


class CExtensionsRule(BaseRule):
    rule_id = "PPY035"
    title = "C extension package may need PyPy compatibility verification"
    runtime = "pypy"
    severity = Severity.INFO

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        imp_map = collect_imports(node)
        seen: set[str] = set()

        for info in imp_map.by_statement():
            base = (info.module or "").split(".")[0]
            if base in KNOWN_PROBLEMATIC and base not in seen:
                seen.add(base)
                findings.append(Finding(
                    file=filename, line=info.line, col=info.col,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        f"'{base}' is a C extension package. PyPy runs "
                        "most such packages through its cpyext "
                        "compatibility layer, which is correctness-"
                        "complete for many widely used packages but "
                        "carries a real performance overhead, and "
                        "per-package/per-version support still varies. "
                        "Some packages now ship native PyPy wheels "
                        "(no cpyext involved); others don't. Verify "
                        "this specific package's current PyPy support "
                        "before deploying, rather than assuming either "
                        "way."
                    ),
                    severity=Severity.INFO,
                    confidence=Confidence.MEDIUM,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        f"Check '{base}''s current PyPy support (native "
                        "wheel vs. cpyext vs. unsupported) at "
                        "https://pypy.org/compat.html or on PyPI before "
                        "deploying on PyPy."
                    ),
                    docs_url="https://doc.pypy.org/en/latest/cpython_differences.html",
                ))
        return findings
