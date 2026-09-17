"""
pyrift.rule_metadata
~~~~~~~~~~~~~~~~~~~~

Authoritative confidence/evidence metadata for reviewed rules.

Rules without an entry intentionally remain at the conservative
Finding defaults:

    confidence = LOW
    evidence_type = INFERRED
    intent_basis = INFERRED

This prevents unreviewed rules from silently claiming HIGH confidence or
claiming that a behavior change was intentional without supporting evidence.

2026-09 taxonomy update
------------------------
Following the architecture review, every rule now also carries:

``category``
    One of ``RuleCategory.SEMANTIC`` / ``COMPATIBILITY`` /
    ``IMPLEMENTATION`` / ``PERFORMANCE``. See ``pyrift.finding`` for the
    precise definitions. Classification below follows the review's own
    worked examples (sections 2 and 47) wherever it gave one explicitly;
    everything else is classified by a conservative, documented
    heuristic (see ``_default_category`` and ``_default_pypy_category``)
    and marked ``taxonomy_reviewed=False`` so that a partial pass is
    never silently presented as a completed audit.

``contract_status``
    What kind of guarantee is at stake (``ContractStatus``): whether a
    symbol/behavior is documented as guaranteed, is deprecated/removed,
    or is explicitly implementation-defined.

``rule_tier``
    PyPy rules only. ``TIER_A`` rules are backed by a specific, citable
    PyPy documentation section describing a concrete difference and keep
    HIGH confidence. ``TIER_B`` rules are legitimate but are primarily
    performance heuristics -- confidence is capped at MEDIUM and the
    category is PERFORMANCE. ``TIER_C`` rules describe a real concern
    that currently rests on broad/general documentation rather than a
    precise, checkable claim -- confidence is capped at MEDIUM pending
    stronger evidence. This is exactly the Tier A/B/C split from the
    review (point 47); ``NOT_TIERED`` rules have not yet been reviewed
    against that rubric and should not be assumed to be Tier A.

``runtime_verification``
    Whether the rule has a corresponding, *complete* entry in
    ``benchmark/runtime_harness.py``. Only rules with probe coverage for
    every version they claim to affect may be ``VERIFIED`` -- see that
    module's module docstring for why "probe missing -> SKIP -> overall
    OK" is not verification (review, point 5).
"""

from __future__ import annotations

from typing import cast

from .finding import (
    Confidence,
    ContractStatus,
    EvidenceType,
    IntentBasis,
    RuleCategory,
    RuleTier,
    RuntimeVerificationState,
)

# Rules with a complete runtime_harness.py entry across every version they
# claim to affect. Keep this in sync with
# ``benchmark.runtime_harness.VERIFIED_RULES`` -- a test asserts they match.
FULLY_RUNTIME_VERIFIED_RULES = {
    "CPY022",
    "CPY027",
    "CPY029",
    "CPY036",
    "CPY038",
    "CPY050",
    "CPY057",
}

# --- CPython rule categorisation --------------------------------------
#
# Rules whose primary claim is a *silent behavior/output* difference
# (the program keeps running, but does something different) rather than
# a hard ImportError/AttributeError at the wrong version. This is
# section 2's "bucket A" from the review, generalised to the full
# CPython rule set using the same standard: does the code keep executing
# while producing a different observable result?
_CPY_SEMANTIC = {
    "CPY001",  # dict ordering assumption
    "CPY008",  # __slots__ may not prevent __dict__
    "CPY022",  # ~True/~False bitwise inversion -- surprising value, not just a future removal
    "CPY023",  # multiprocessing default start method
    "CPY029",  # locals() semantics
    "CPY030",  # sys.path bytes entries
    "CPY038",  # asyncio.get_event_loop()
    "CPY045",  # NaN hash
    "CPY046",  # open() without encoding
    "CPY054",  # int() / __trunc__
    "CPY055",  # NotImplemented in bool context
    "CPY057",  # pickle default protocol
}

# Rules about a build/runtime *configuration* dimension (free-threading)
# rather than a Python-version boundary or a pure API in/out change.
_CPY_IMPLEMENTATION = {
    "CPY051",  # free-threaded module-level mutable state
}

_REMOVED_TITLE_MARKERS = ("removed",)
_DEPRECATED_TITLE_MARKERS = ("deprecated",)


def _default_cpy_category(rule_id: str) -> RuleCategory:
    if rule_id in _CPY_SEMANTIC:
        return RuleCategory.SEMANTIC
    if rule_id in _CPY_IMPLEMENTATION:
        return RuleCategory.IMPLEMENTATION
    return RuleCategory.COMPATIBILITY


def _default_cpy_contract(rule_id: str, title: str) -> ContractStatus:
    if rule_id in _CPY_IMPLEMENTATION:
        return ContractStatus.IMPLEMENTATION_DEFINED
    lowered = title.lower()
    if any(marker in lowered for marker in _REMOVED_TITLE_MARKERS):
        return ContractStatus.REMOVED
    if any(marker in lowered for marker in _DEPRECATED_TITLE_MARKERS):
        return ContractStatus.DEPRECATED
    return ContractStatus.DOCUMENTED


# --- PyPy tier classification (review, point 47) -----------------------

TIER_A = {
    "PPY001", "PPY003", "PPY004", "PPY009", "PPY013", "PPY014", "PPY016",
    "PPY017", "PPY019", "PPY025", "PPY026", "PPY028", "PPY029", "PPY031",
    "PPY032", "PPY034", "PPY045",
}

TIER_B = {"PPY027", "PPY038", "PPY042", "PPY049"}

TIER_C = {
    "PPY002", "PPY005", "PPY018", "PPY021", "PPY030", "PPY035", "PPY036",
    "PPY037", "PPY039", "PPY040", "PPY041", "PPY044", "PPY047", "PPY051",
    "PPY052", "PPY053",
}

# PPY011 ("array.array('u') removed in Python 3.13") is a CPython version
# fact, not a PyPy/CPython implementation difference, despite living in
# the PyPy rule package (README already marks its runtime as "both").
_PPY_COMPATIBILITY_OVERRIDE = {"PPY011"}


def _default_pypy_category(rule_id: str) -> RuleCategory:
    if rule_id in _PPY_COMPATIBILITY_OVERRIDE:
        return RuleCategory.COMPATIBILITY
    if rule_id in TIER_B:
        return RuleCategory.PERFORMANCE
    return RuleCategory.IMPLEMENTATION


def _default_pypy_tier(rule_id: str) -> RuleTier:
    if rule_id in TIER_A:
        return RuleTier.TIER_A
    if rule_id in TIER_B:
        return RuleTier.TIER_B
    if rule_id in TIER_C:
        return RuleTier.TIER_C
    return RuleTier.NOT_TIERED


def _metadata(
    confidence: str,
    evidence: str,
    *,
    status: str = "active",
    last_verified: str = "",
    affected_versions: str = "",
    intent_basis: str | None = None,
    category: RuleCategory | None = None,
    contract_status: ContractStatus | None = None,
    rule_tier: RuleTier = RuleTier.NOT_TIERED,
    claim_confidence: str | None = None,
    detection_confidence: str | None = None,
    platform_scope: str = "",
    taxonomy_reviewed: bool = False,
) -> dict[str, object]:
    if evidence.startswith("pep:"):
        evidence_type = EvidenceType.PEP
        evidence_source = evidence
    elif evidence == "official_docs":
        evidence_type = EvidenceType.OFFICIAL_DOCS
        evidence_source = evidence
    elif evidence == "runtime_probe":
        evidence_type = EvidenceType.RUNTIME_PROBE
        evidence_source = evidence
    elif evidence == "observed":
        evidence_type = EvidenceType.OBSERVED
        evidence_source = evidence
    elif evidence == "inferred":
        evidence_type = EvidenceType.INFERRED
        evidence_source = evidence
    elif evidence == "deprecation_warn":
        evidence_type = EvidenceType.DEPRECATION_WARN
        evidence_source = evidence
    else:
        raise ValueError(f"Unknown evidence type: {evidence}")

    if intent_basis is None:
        intent_basis = {
            EvidenceType.PEP: IntentBasis.DOCUMENTED.value,
            EvidenceType.OFFICIAL_DOCS: IntentBasis.DOCUMENTED.value,
            EvidenceType.DEPRECATION_WARN: IntentBasis.DEPRECATION.value,
            EvidenceType.RUNTIME_PROBE: IntentBasis.OBSERVED.value,
            EvidenceType.OBSERVED: IntentBasis.OBSERVED.value,
            EvidenceType.INFERRED: IntentBasis.INFERRED.value,
        }[evidence_type]

    entry: dict[str, object] = {
        "confidence": Confidence(confidence),
        "claim_confidence": Confidence(claim_confidence) if claim_confidence else Confidence(confidence),
        "detection_confidence": Confidence(detection_confidence) if detection_confidence else Confidence(confidence),
        "evidence_type": evidence_type,
        "evidence_source": evidence_source,
        "intent_basis": IntentBasis(intent_basis),
        "status": status,
        "last_verified": last_verified,
        "affected_versions": affected_versions,
        "rule_tier": rule_tier,
        "runtime_verification": RuntimeVerificationState.NOT_APPLICABLE,
        "platform_scope": platform_scope,
        "taxonomy_reviewed": taxonomy_reviewed,
    }
    if category is not None:
        entry["category"] = category
    if contract_status is not None:
        entry["contract_status"] = contract_status
    return entry


REQUIRED_METADATA_FIELDS = (
    "confidence",
    "evidence_type",
    "evidence_source",
    "intent_basis",
    "status",
    "last_verified",
)


def validate_metadata() -> bool:
    """Return True when all reviewed metadata is complete and consistent."""
    default_intent = {
        EvidenceType.PEP: IntentBasis.DOCUMENTED,
        EvidenceType.OFFICIAL_DOCS: IntentBasis.DOCUMENTED,
        EvidenceType.DEPRECATION_WARN: IntentBasis.DEPRECATION,
        EvidenceType.RUNTIME_PROBE: IntentBasis.OBSERVED,
        EvidenceType.OBSERVED: IntentBasis.OBSERVED,
        EvidenceType.INFERRED: IntentBasis.INFERRED,
    }

    for entry in RULE_METADATA.values():
        for field in REQUIRED_METADATA_FIELDS:
            if field not in entry:
                return False

        evidence_type = entry["evidence_type"]
        intent_basis = entry["intent_basis"]
        if not isinstance(evidence_type, EvidenceType):  # pragma: no cover
            return False
        if not isinstance(intent_basis, IntentBasis):  # pragma: no cover
            return False
        if (  # pragma: no cover
            intent_basis != IntentBasis.IMPLEMENTATION_DEFINED
            and intent_basis != default_intent[evidence_type]
        ):
            return False

        # A rule can never claim overall HIGH confidence while claiming a
        # weaker score on either contributing dimension (review #24/#58).
        order = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}
        confidence = cast(Confidence, entry["confidence"])
        claim = cast(Confidence, entry.get("claim_confidence", confidence))
        detection = cast(
            Confidence,
            entry.get("detection_confidence", confidence),
        )
        if order[confidence] > min(order[claim], order[detection]):  # pragma: no cover
            return False

    return True


# --- CPython rule titles, for automatic contract-status classification -
_CPY_TITLES = {
    "CPY001": "Dict ordering assumption",
    "CPY002": "Exception.add_note() requires Python 3.11+",
    "CPY003": "X | Y union type syntax requires Python 3.10+",
    "CPY004": "tomllib requires Python 3.11+",
    "CPY005": "match/case requires Python 3.10+",
    "CPY006": "asyncio.timeout() / TaskGroup requires Python 3.11+",
    "CPY007": "Module removed in Python 3.13",
    "CPY008": "__slots__ may not prevent __dict__ on Python < 3.10",
    "CPY009": "ExceptionGroup requires Python 3.11+",
    "CPY010": "@dataclass(slots=True) requires Python 3.10+",
    "CPY011": "typing.Self requires Python 3.11+",
    "CPY012": "typing.LiteralString requires Python 3.11+",
    "CPY013": "typing.override requires Python 3.12+",
    "CPY014": "typing.TypeAlias requires Python 3.10+",
    "CPY015": "typing.Never requires Python 3.11+",
    "CPY016": "typing.TypeVarTuple requires Python 3.11+",
    "CPY017": "typing.Unpack requires Python 3.11+",
    "CPY018": "typing.Required / NotRequired requires Python 3.11+",
    "CPY019": "distutils removed in Python 3.12+",
    "CPY020": "datetime.UTC requires Python 3.11+",
    "CPY022": "Bitwise inversion on bool (~True/~False) deprecated in 3.12",
    "CPY023": "multiprocessing default start method changing in Python 3.14",
    "CPY024": "typing.TypeGuard requires Python 3.10+",
    "CPY025": "typing.ParamSpec requires Python 3.10+",
    "CPY026": "typing.io and typing.re removed in Python 3.13",
    "CPY027": "locale.resetlocale() removed in Python 3.13",
    "CPY028": "lib2to3 removed in Python 3.13",
    "CPY029": "locals() semantics changed in Python 3.13 (PEP 667)",
    "CPY030": "sys.path no longer accepts bytes entries in Python 3.11+",
    "CPY031": "typing.assert_never requires Python 3.11+",
    "CPY032": "typing.reveal_type requires Python 3.11+",
    "CPY033": "pathlib.Path.is_relative_to() requires Python 3.9+",
    "CPY034": "int.bit_count() requires Python 3.10+",
    "CPY035": "str.removeprefix/removesuffix requires Python 3.9+",
    "CPY036": "datetime.utcnow() deprecated since Python 3.12",
    "CPY037": "datetime.utcfromtimestamp() deprecated since Python 3.12",
    "CPY038": "asyncio.get_event_loop() raises RuntimeError in Python 3.14+",
    "CPY039": "zoneinfo module requires Python 3.9+",
    "CPY040": "graphlib module requires Python 3.9+",
    "CPY041": "dict | merge operator requires Python 3.9+",
    "CPY042": "aiter() and anext() builtins require Python 3.10+",
    "CPY043": "math.lcm() requires Python 3.9+",
    "CPY044": "math.gcd() with multiple args requires Python 3.9+",
    "CPY045": "NaN hash behaviour changed in Python 3.10",
    "CPY046": "open() without encoding= uses platform-dependent encoding before 3.15",
    "CPY047": "collections.abc.ByteString deprecated, scheduled removal in Python 3.17",
    "CPY048": "concurrent.interpreters requires Python 3.14+",
    "CPY049": "compression.zstd requires Python 3.14+",
    "CPY050": "PurePath.is_reserved() deprecated in 3.13, removed in 3.15",
    "CPY051": "Module-level mutable state may require synchronization in free-threaded Python",
    "CPY053": "typing.get_overloads() requires Python 3.11+",
    "CPY054": "int() no longer delegates to __trunc__() in Python 3.14",
    "CPY055": "NotImplemented in boolean context raises TypeError in Python 3.14",
    "CPY057": "pickle default protocol changed to 5 in Python 3.14",
    "CPY062": "string.templatelib requires Python 3.14+",
    "CPY063": "annotationlib requires Python 3.14+",
    "CPY064": "Deprecated AST node types removed in Python 3.14",
    "CPY065": "pkgutil.find_loader()/get_loader() removed in Python 3.14",
    "CPY066": "asyncio child watcher classes removed in Python 3.14",
    "CPY067": "typing.NamedTuple keyword syntax removed in Python 3.15",
    "CPY068": "typing.no_type_check_decorator deprecated in 3.13, removed in 3.15",
    "CPY069": "asyncio.iscoroutinefunction() deprecated in Python 3.14",
    "CPY070": "asyncio event loop policy deprecated in Python 3.14",
    "CPY071": "pty.master_open()/slave_open() removed in Python 3.14",
    "CPY072": "importlib.abc resource classes removed in Python 3.14",
    "CPY073": "sqlite3.version/version_info removed in Python 3.14",
    "CPY074": "code.__lnotab__ deprecated since Python 3.10 (PEP 626)",
    "CPY075": "http.server.CGIHTTPRequestHandler deprecated in 3.13, removed in 3.15",
    "CPY076": "ssl.wrap_socket() removed in Python 3.12",
    "CPY077": "typing.TypedDict zero-field syntax removed in Python 3.15",
    "CPY078": "functools.reduce() keyword arguments deprecated, removal scheduled for 3.16",
}


def _cpy(confidence: str, evidence: str, rule_id: str, **kwargs: object) -> dict[str, object]:
    kwargs.setdefault("category", _default_cpy_category(rule_id))
    kwargs.setdefault(
        "contract_status",
        _default_cpy_contract(rule_id, _CPY_TITLES.get(rule_id, "")),
    )
    if rule_id in FULLY_RUNTIME_VERIFIED_RULES:
        kwargs.setdefault("taxonomy_reviewed", True)
    entry = _metadata(confidence, evidence, **kwargs)  # type: ignore[arg-type]
    if rule_id in FULLY_RUNTIME_VERIFIED_RULES:
        entry["runtime_verification"] = RuntimeVerificationState.VERIFIED
    return entry


def _ppy(confidence: str, evidence: str, rule_id: str, **kwargs: object) -> dict[str, object]:
    kwargs.setdefault("category", _default_pypy_category(rule_id))
    kwargs.setdefault("rule_tier", _default_pypy_tier(rule_id))
    kwargs.setdefault("contract_status", ContractStatus.IMPLEMENTATION_DEFINED)
    tier = kwargs["rule_tier"]
    kwargs["taxonomy_reviewed"] = tier != RuleTier.NOT_TIERED
    return _metadata(confidence, evidence, **kwargs)  # type: ignore[arg-type]


RULE_METADATA: dict[str, dict[str, object]] = {
    "CPY001": _cpy("high", "official_docs", "CPY001", last_verified="2026-08-29"),
    "CPY002": _cpy("high", "pep:678", "CPY002", last_verified="2026-08-29"),
    "CPY003": _cpy("high", "pep:604", "CPY003", last_verified="2026-08-29"),
    "CPY004": _cpy("high", "pep:680", "CPY004", last_verified="2026-08-29"),
    "CPY005": _cpy("high", "pep:634", "CPY005", last_verified="2026-08-29"),
    "CPY006": _cpy("high", "official_docs", "CPY006", last_verified="2026-08-29"),
    "CPY007": _cpy("high", "pep:594", "CPY007", last_verified="2026-08-29", affected_versions=">=3.13"),
    "CPY008": _cpy("medium", "official_docs", "CPY008", last_verified="2026-08-29"),
    "CPY009": _cpy("high", "pep:654", "CPY009", last_verified="2026-08-29"),
    "CPY010": _cpy("high", "official_docs", "CPY010", last_verified="2026-08-29"),
    "CPY011": _cpy("high", "pep:673", "CPY011", last_verified="2026-08-29"),
    "CPY012": _cpy("high", "pep:675", "CPY012", last_verified="2026-08-29"),
    "CPY013": _cpy("high", "pep:698", "CPY013", last_verified="2026-08-29"),
    "CPY014": _cpy("high", "pep:613", "CPY014", last_verified="2026-08-29"),
    "CPY015": _cpy("high", "pep:673", "CPY015", last_verified="2026-08-29"),
    "CPY016": _cpy("high", "pep:646", "CPY016", last_verified="2026-08-29"),
    "CPY017": _cpy("high", "pep:646", "CPY017", last_verified="2026-08-29"),
    "CPY018": _cpy("high", "pep:655", "CPY018", last_verified="2026-08-29"),
    "CPY019": _cpy("high", "pep:632", "CPY019", last_verified="2026-08-29"),
    "CPY020": _cpy("high", "official_docs", "CPY020", last_verified="2026-08-29"),
    "CPY022": _cpy("high", "deprecation_warn", "CPY022", last_verified="2026-08-29"),
    "CPY023": _cpy(
        "medium", "official_docs", "CPY023", last_verified="2026-08-29",
        detection_confidence="medium",
        platform_scope="posix_non_macos",
    ),
    "CPY024": _cpy("high", "pep:647", "CPY024", last_verified="2026-08-29"),
    "CPY025": _cpy("high", "pep:612", "CPY025", last_verified="2026-08-29"),
    "CPY026": _cpy("high", "official_docs", "CPY026", last_verified="2026-08-29"),
    "CPY027": _cpy("high", "deprecation_warn", "CPY027", last_verified="2026-08-29"),
    "CPY028": _cpy("high", "official_docs", "CPY028", last_verified="2026-08-29"),
    "CPY029": _cpy(
        "high", "pep:667", "CPY029", last_verified="2026-08-29",
        intent_basis="implementation_defined",
    ),
    "CPY030": _cpy("high", "official_docs", "CPY030", last_verified="2026-08-29"),
    "CPY031": _cpy("high", "official_docs", "CPY031", last_verified="2026-09-13"),
    "CPY032": _cpy("high", "official_docs", "CPY032", last_verified="2026-09-13"),
    "CPY033": _cpy("high", "official_docs", "CPY033", last_verified="2026-08-29"),
    "CPY034": _cpy("high", "official_docs", "CPY034", last_verified="2026-08-29"),
    "CPY035": _cpy("high", "pep:616", "CPY035", last_verified="2026-08-29"),
    "CPY036": _cpy("high", "deprecation_warn", "CPY036", last_verified="2026-08-29"),
    "CPY037": _cpy("high", "deprecation_warn", "CPY037", last_verified="2026-08-29"),
    "CPY038": _cpy("high", "official_docs", "CPY038", last_verified="2026-08-29"),
    "CPY039": _cpy("high", "pep:615", "CPY039", last_verified="2026-08-29"),
    "CPY040": _cpy("high", "official_docs", "CPY040", last_verified="2026-08-29"),
    "CPY041": _cpy("high", "pep:584", "CPY041", last_verified="2026-08-29"),
    "CPY042": _cpy("high", "official_docs", "CPY042", last_verified="2026-08-29"),
    "CPY043": _cpy("high", "official_docs", "CPY043", last_verified="2026-08-29"),
    "CPY044": _cpy("high", "official_docs", "CPY044", last_verified="2026-08-29"),
    "CPY045": _cpy("high", "official_docs", "CPY045", last_verified="2026-08-29"),
    "CPY046": _cpy("high", "pep:686", "CPY046", last_verified="2026-08-29", affected_versions="<=3.14"),
    "CPY047": _cpy("high", "official_docs", "CPY047", last_verified="2026-08-29"),
    "CPY048": _cpy("high", "pep:734", "CPY048", last_verified="2026-08-29"),
    "CPY049": _cpy("high", "official_docs", "CPY049", last_verified="2026-08-29"),
    "CPY050": _cpy("high", "deprecation_warn", "CPY050", last_verified="2026-08-29"),
    "CPY051": _cpy(
        "medium", "pep:703", "CPY051", last_verified="2026-08-29",
        claim_confidence="medium",
    ),
    "CPY053": _cpy("high", "official_docs", "CPY053", last_verified="2026-08-29"),
    "CPY054": _cpy("high", "official_docs", "CPY054", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY055": _cpy("high", "official_docs", "CPY055", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY057": _cpy("high", "official_docs", "CPY057", last_verified="2026-08-29"),
    "CPY062": _cpy("high", "pep:750", "CPY062", last_verified="2026-08-29"),
    "CPY063": _cpy("high", "pep:749", "CPY063", last_verified="2026-08-29"),
    "CPY064": _cpy("high", "official_docs", "CPY064", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY065": _cpy("high", "official_docs", "CPY065", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY066": _cpy("high", "official_docs", "CPY066", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY067": _cpy("high", "deprecation_warn", "CPY067", last_verified="2026-08-29", affected_versions=">=3.13,<3.15"),
    "CPY068": _cpy("high", "deprecation_warn", "CPY068", last_verified="2026-08-29", affected_versions=">=3.13,<3.15"),
    "CPY069": _cpy("high", "deprecation_warn", "CPY069", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY070": _cpy("high", "deprecation_warn", "CPY070", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY071": _cpy("high", "official_docs", "CPY071", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY072": _cpy("high", "official_docs", "CPY072", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY073": _cpy("high", "official_docs", "CPY073", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY074": _cpy("high", "pep:626", "CPY074", last_verified="2026-08-29", affected_versions=">=3.10"),
    "CPY075": _cpy("high", "deprecation_warn", "CPY075", last_verified="2026-08-29", affected_versions=">=3.13,<3.15"),
    "CPY076": _cpy("high", "official_docs", "CPY076", last_verified="2026-08-29", affected_versions=">=3.12"),
    "CPY077": _cpy("high", "deprecation_warn", "CPY077", last_verified="2026-08-29", affected_versions=">=3.13,<3.15"),
    "CPY078": _cpy("high", "official_docs", "CPY078", last_verified="2026-09-17", affected_versions=">=3.14,<3.16"),
    "PPY001": _ppy("high", "official_docs", "PPY001", last_verified="2026-08-29"),
    "PPY002": _ppy("medium", "official_docs", "PPY002", last_verified="2026-08-29"),
    "PPY003": _ppy("high", "official_docs", "PPY003", last_verified="2026-08-29"),
    "PPY004": _ppy("high", "official_docs", "PPY004", last_verified="2026-08-29"),
    "PPY005": _ppy("medium", "official_docs", "PPY005", last_verified="2026-08-29"),
    "PPY006": _ppy("high", "official_docs", "PPY006", last_verified="2026-08-29"),
    "PPY007": _ppy("low", "observed", "PPY007", last_verified="2026-08-29"),
    "PPY008": _ppy("high", "official_docs", "PPY008", last_verified="2026-08-29"),
    "PPY009": _ppy("high", "official_docs", "PPY009", last_verified="2026-08-29"),
    "PPY010": _ppy("high", "official_docs", "PPY010", last_verified="2026-08-29"),
    "PPY011": _ppy("high", "official_docs", "PPY011", last_verified="2026-08-29"),
    "PPY012": _ppy("high", "official_docs", "PPY012", last_verified="2026-08-29"),
    "PPY013": _ppy("high", "official_docs", "PPY013", last_verified="2026-08-29"),
    "PPY014": _ppy(
        "high", "official_docs", "PPY014", last_verified="2026-09-17",
        category=RuleCategory.PERFORMANCE,
    ),
    "PPY015": _ppy("high", "official_docs", "PPY015", last_verified="2026-08-29"),
    "PPY016": _ppy("high", "official_docs", "PPY016", last_verified="2026-08-29"),
    "PPY017": _ppy("high", "official_docs", "PPY017", last_verified="2026-08-29"),
    "PPY018": _ppy("medium", "official_docs", "PPY018", last_verified="2026-08-29"),
    "PPY019": _ppy("high", "official_docs", "PPY019", last_verified="2026-08-29"),
    "PPY021": _ppy("medium", "official_docs", "PPY021", last_verified="2026-08-29"),
    "PPY022": _ppy("high", "official_docs", "PPY022", last_verified="2026-08-29"),
    "PPY023": _ppy("high", "official_docs", "PPY023", last_verified="2026-08-29"),
    "PPY024": _ppy("high", "official_docs", "PPY024", last_verified="2026-08-29"),
    "PPY025": _ppy("high", "official_docs", "PPY025", last_verified="2026-08-29"),
    "PPY026": _ppy("high", "official_docs", "PPY026", last_verified="2026-08-29"),
    "PPY027": _ppy("medium", "official_docs", "PPY027", last_verified="2026-08-29"),
    "PPY028": _ppy("high", "official_docs", "PPY028", last_verified="2026-08-29"),
    "PPY029": _ppy("high", "official_docs", "PPY029", last_verified="2026-08-29"),
    "PPY030": _ppy("medium", "official_docs", "PPY030", last_verified="2026-08-29"),
    "PPY031": _ppy("high", "official_docs", "PPY031", last_verified="2026-08-29"),
    "PPY032": _ppy("high", "official_docs", "PPY032", last_verified="2026-08-29"),
    "PPY033": _ppy("medium", "inferred", "PPY033", last_verified="2026-08-29"),
    "PPY034": _ppy("high", "official_docs", "PPY034", last_verified="2026-08-29"),
    "PPY035": _ppy(
        "medium", "official_docs", "PPY035", last_verified="2026-09-17",
        claim_confidence="medium",
    ),
    "PPY036": _ppy("medium", "official_docs", "PPY036", last_verified="2026-08-29"),
    "PPY037": _ppy("low", "observed", "PPY037", last_verified="2026-08-29"),
    "PPY038": _ppy("medium", "official_docs", "PPY038", last_verified="2026-08-29"),
    "PPY039": _ppy("low", "observed", "PPY039", last_verified="2026-08-29"),
    "PPY040": _ppy(
        "high", "official_docs", "PPY040", last_verified="2026-09-17",
    ),
    "PPY041": _ppy("high", "pep:584", "PPY041", last_verified="2026-08-29"),
    "PPY042": _ppy("low", "observed", "PPY042", last_verified="2026-08-29"),
    "PPY044": _ppy("medium", "inferred", "PPY044", last_verified="2026-08-29"),
    "PPY045": _ppy("high", "official_docs", "PPY045", last_verified="2026-08-29"),
    "PPY047": _ppy("medium", "official_docs", "PPY047", last_verified="2026-08-29"),
    "PPY049": _ppy("medium", "official_docs", "PPY049", last_verified="2026-08-29"),
    "PPY051": _ppy("medium", "observed", "PPY051", last_verified="2026-08-29"),
    "PPY052": _ppy("low", "observed", "PPY052", last_verified="2026-08-29"),
    "PPY053": _ppy(
        "low", "observed", "PPY053", last_verified="2026-08-29",
        status="experimental",
    ),
}
