"""
pyrift.finding
~~~~~~~~~~~~~~
The Finding dataclass — every rule returns a list of these.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import cast


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Confidence(str, Enum):
    """How certain pyrift is that this finding is a real issue."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceType(str, Enum):
    """What kind of evidence backs this rule.

    Evidence describes how the behavior was established; it does not by
    itself prove that a behavior change was intentional. ``IntentBasis``
    records the stronger compatibility/intent evidence separately.
    """

    OFFICIAL_DOCS = "official_docs"
    RUNTIME_PROBE = "runtime_probe"
    DEPRECATION_WARN = "deprecation_warn"
    PEP = "pep"
    OBSERVED = "observed"
    INFERRED = "inferred"


class IntentBasis(str, Enum):
    """What PyRift can establish about the status of a behavior change.

    ``DOCUMENTED`` and ``DEPRECATION`` are the only bases that directly
    establish an intentional, documented compatibility change. ``OBSERVED``
    means a runtime difference is known but intent is not established.
    ``IMPLEMENTATION_DEFINED`` means the documented contract leaves room for
    implementation-specific behavior. ``INFERRED`` is the most conservative
    classification and does not claim maintainer intent.
    """

    DOCUMENTED = "documented"
    DEPRECATION = "deprecation"
    IMPLEMENTATION_DEFINED = "implementation_defined"
    OBSERVED = "observed"
    INFERRED = "inferred"


class Runtime(str, Enum):
    CPYTHON = "cpython"
    PYPY = "pypy"
    BOTH = "both"


class RuleCategory(str, Enum):
    """What kind of claim a rule is making.

    This is the taxonomy split requested in the 2026-09 architecture
    review: PyRift's rule catalog mixes three materially different kinds
    of claims, and treating them identically ("compatibility") hides that
    difference from the reader.

    SEMANTIC
        The program keeps running but observable behavior/output differs
        (dict ordering assumptions, ``locals()`` semantics, NaN hashing,
        pickle's default protocol, GC/finalizer timing, ...).
    COMPATIBILITY
        A name/attribute/module is introduced, deprecated, or removed at
        a specific version. The primary failure mode is
        ImportError/AttributeError/SyntaxError, not a silent behavior
        change.
    IMPLEMENTATION
        A documented difference between CPython and another implementation
        (usually PyPy) that is not primarily about raw speed -- id()
        stability, ctypes support, monkey-patching, hash() values, etc.
    PERFORMANCE
        An implementation detail that affects speed/complexity but not
        correctness (string concatenation complexity, attribute-deletion
        speed, timeit semantics, ...).
    """

    SEMANTIC = "semantic"
    COMPATIBILITY = "compatibility"
    IMPLEMENTATION = "implementation"
    PERFORMANCE = "performance"


class ContractStatus(str, Enum):
    """What kind of guarantee (or lack of one) backs the affected behavior.

    This is distinct from ``IntentBasis``: ``IntentBasis`` describes what
    PyRift can establish about *why* a rule exists (documented change vs.
    inference). ``ContractStatus`` describes the strength of the
    underlying language/library guarantee that the finding concerns.
    """

    GUARANTEED = "guaranteed"
    DOCUMENTED = "documented"
    IMPLEMENTATION_DEFINED = "implementation_defined"
    DEPRECATED = "deprecated"
    REMOVED = "removed"
    OBSERVED = "observed"
    UNKNOWN = "unknown"


class RuntimeVerificationState(str, Enum):
    """How thoroughly a rule's runtime claim has actually been checked.

    ``VERIFIED`` may only be used for rules with a passing entry in
    ``benchmark/runtime_harness.py`` for *every* version range the rule
    claims to affect. Rules with partial probe coverage, or none, must
    not be reported as verified -- see the 2026-09 review, point 5:
    treating "probe file missing -> SKIP -> overall OK" as verification
    is a credibility problem, not a convenience.
    """

    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    NOT_APPLICABLE = "not_applicable"


class RuleTier(str, Enum):
    """Editorial confidence tier used for the PyPy rule audit (review #47).

    TIER_A rules are backed by specific, citable PyPy documentation of a
    concrete behavior difference and are safe to present as high
    confidence. TIER_B rules are legitimate but are primarily performance
    heuristics and should not be presented with the same certainty as a
    documented API/behavior difference. TIER_C rules describe a real
    concern but currently rest on general/broad documentation rather
    than a precise, checkable claim, and need stronger evidence before
    they are promoted.
    """

    TIER_A = "tier_a"
    TIER_B = "tier_b"
    TIER_C = "tier_c"
    NOT_TIERED = "not_tiered"


_VERSION_RE = re.compile(
    r"^\s*(>=|<=|==|!=|>|<)?\s*(\d+\.\d+(?:\.\d+)?)\s*$"
)


def parse_version_range(spec: str) -> tuple[str, str]:
    """Parse a version expression into ``(from, until)`` strings.

    Supported forms::

        ">=3.13"           -> ("3.13", "")
        "<3.15"            -> ("", "3.15")
        ">=3.10,<3.14"     -> ("3.10", "3.14")
        ">=3.13, <3.16"    -> ("3.13", "3.16")
        ""                 -> ("", "")

    ``from`` is inclusive, ``until`` is exclusive.
    """
    if not spec or not spec.strip():
        return ("", "")

    from_ver = ""
    until_ver = ""

    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = _VERSION_RE.match(part)
        if m is None:
            continue
        op = m.group(1) or "=="
        ver = m.group(2)

        if op in (">=", ">"):
            from_ver = ver
        elif op in ("<=", "<"):
            until_ver = ver
        elif op == "==":
            from_ver = ver
            until_ver = ver
        elif op == "!=":
            pass  # excluded version — no range info

    return (from_ver, until_ver)


@dataclass
class Finding:
    """A single detected behaviour difference."""

    # Where
    file: str
    line: int
    col: int = 0

    # What
    rule_id: str = ""
    title: str = ""
    description: str = ""
    severity: Severity = Severity.WARNING

    # Confidence/evidence
    #
    # LOW/INFERRED are intentionally conservative defaults. A static
    # analyzer must not claim high confidence without documented evidence.
    #
    # ``confidence`` is retained for backward compatibility (existing
    # consumers, SARIF/JSON output, CLI filters). It is derived as the
    # *weakest* of the multidimensional scores below unless a caller sets
    # it explicitly, so it can never silently overstate certainty.
    confidence: Confidence = Confidence.LOW
    evidence_type: EvidenceType = EvidenceType.INFERRED
    evidence_source: str = ""
    intent_basis: IntentBasis = IntentBasis.INFERRED

    # Multidimensional confidence (review #24, #61).
    # claim_confidence:     how solid is the underlying behavioral claim?
    # detection_confidence: how precisely does the AST pattern match the
    #                       claim (vs. a proxy pattern that may not apply)?
    # runtime_verification: was this actually executed and observed, or
    #                       only documented/inferred?
    claim_confidence: Confidence = Confidence.LOW
    detection_confidence: Confidence = Confidence.LOW
    runtime_verification: RuntimeVerificationState = (
        RuntimeVerificationState.NOT_APPLICABLE
    )

    # What kind of claim/guarantee this finding rests on.
    category: RuleCategory | str = RuleCategory.COMPATIBILITY
    contract_status: ContractStatus = ContractStatus.UNKNOWN
    rule_tier: RuleTier = RuleTier.NOT_TIERED

    # Which runtimes / versions are affected
    runtime: Runtime = Runtime.BOTH
    affected_from: str = ""
    affected_until: str = ""
    platform_scope: str = ""

    # Rule lifecycle (populated from rule_metadata)
    rule_status: str = ""
    rule_last_verified: str = ""

    # Fix guidance
    suggestion: str = ""
    docs_url: str = ""

    # Context-sensitive confidence note. Set by the scanner's guard/shim
    # suppression pass (see pyrift.analysis.guards) when project context
    # (a version guard, an implementation guard, or a try/except
    # compatibility shim) makes a finding's *contextual* risk lower than
    # its rule-level confidence would suggest, without fully suppressing
    # it. Empty when no such context applies.
    context_note: str = ""

    def __post_init__(self) -> None:
        """Attach reviewed rule metadata when available."""
        try:
            from .rule_metadata import RULE_METADATA
        except ImportError:  # pragma: no cover
            return

        metadata = RULE_METADATA.get(self.rule_id)
        if metadata is None:  # pragma: no cover
            return

        self.confidence = cast(Confidence, metadata["confidence"])
        self.evidence_type = cast(EvidenceType, metadata["evidence_type"])
        self.evidence_source = str(metadata["evidence_source"])
        self.intent_basis = cast(IntentBasis, metadata["intent_basis"])
        self.rule_status = str(metadata.get("status", ""))
        self.rule_last_verified = str(metadata.get("last_verified", ""))

        category = metadata.get("category")
        if category is not None:
            self.category = cast(RuleCategory, category)

        contract_status = metadata.get("contract_status")
        if contract_status is not None:
            self.contract_status = cast(ContractStatus, contract_status)

        self.rule_tier = cast(
            RuleTier,
            metadata.get("rule_tier", self.rule_tier),
        )

        claim_conf = metadata.get("claim_confidence")
        self.claim_confidence = (
            cast(Confidence, claim_conf)
            if claim_conf is not None
            else self.confidence
        )

        detect_conf = metadata.get("detection_confidence")
        self.detection_confidence = (
            cast(Confidence, detect_conf)
            if detect_conf is not None
            else self.confidence
        )

        runtime_verif = metadata.get("runtime_verification")
        if runtime_verif is not None:
            self.runtime_verification = cast(
                RuntimeVerificationState,
                runtime_verif,
            )

        # ``confidence`` must never exceed the weakest contributing
        # dimension -- this is what makes "HIGH" mean something (review
        # #24, #58): a rule cannot be high confidence overall if its
        # detection heuristic is weak, even if the underlying claim is
        # rock solid.
        _order = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}
        weakest = min(
            (self.confidence, self.claim_confidence, self.detection_confidence),
            key=lambda c: _order[c],
        )
        self.confidence = weakest

        affected_versions = str(metadata.get("affected_versions", ""))
        if affected_versions and not self.affected_from and not self.affected_until:
            self.affected_from, self.affected_until = parse_version_range(
                affected_versions
            )

        platform_scope = metadata.get("platform_scope")
        if platform_scope and not self.platform_scope:
            self.platform_scope = str(platform_scope)

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line}"
        if self.col:  # pragma: no branch
            loc += f":{self.col}"

        sev = self.severity.value.upper()
        conf = self.confidence.value[0].upper()

        return (
            f"[{sev}/{conf}] {loc}  "
            f"{self.rule_id}: {self.title}"
        )

    def to_dict(self) -> dict:
        category = self.category.value if isinstance(self.category, RuleCategory) else self.category
        return {
            "file": self.file,
            "line": self.line,
            "col": self.col,
            "rule_id": self.rule_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "claim_confidence": self.claim_confidence.value,
            "detection_confidence": self.detection_confidence.value,
            "runtime_verification": self.runtime_verification.value,
            "evidence_type": self.evidence_type.value,
            "evidence_source": self.evidence_source,
            "intent_basis": self.intent_basis.value,
            "contract_status": self.contract_status.value,
            "rule_tier": self.rule_tier.value,
            "rule_status": self.rule_status,
            "rule_last_verified": self.rule_last_verified,
            "runtime": self.runtime.value,
            "affected_from": self.affected_from,
            "affected_until": self.affected_until,
            "platform_scope": self.platform_scope,
            "suggestion": self.suggestion,
            "docs_url": self.docs_url,
            "category": category,
            "context_note": self.context_note,
        }