# Behavior evidence and intentionality

PyRift does **not** try to infer CPython maintainer intent from a runtime
result alone. A runtime difference answers **"does this behave differently?"**;
it does not, by itself, answer **"was the change intentional?"**.

For public APIs, this distinction is especially important because CPython
follows a backwards-compatibility policy: incompatible behavior normally goes
through a documented/deprecation path, while implementation details may have
weaker compatibility guarantees.

The scanner therefore keeps two separate pieces of metadata:

- `evidence_type`: how the behavior was established (PEP, official docs,
  runtime probe, deprecation warning, observation, or inference).
- `intent_basis`: what PyRift can establish about the compatibility status of
  that behavior from the available evidence.

## Intent basis

| Basis | Meaning | Can it establish intentional change? |
|---|---|---|
| `documented` | A PEP or official CPython/Python documentation describes the API or behavior/change. | Yes, when the source explicitly documents the compatibility change. |
| `deprecation` | The behavior follows an explicit deprecation/removal path. | Yes. This is the strongest signal for a planned compatibility change. |
| `implementation_defined` | The documented language/API contract leaves behavior to the implementation, or explicitly describes it as implementation-specific. | No. It establishes that implementations may differ. |
| `observed` | A runtime probe or empirical observation establishes a difference. | No. It establishes behavior, not maintainer intent. |
| `inferred` | The rule is based on static reasoning without stronger authoritative evidence. | No. |

Unreviewed rules default to `LOW` confidence, `INFERRED` evidence, and
`INFERRED` intent basis.

## How CPython compatibility changes are established

For public Python APIs, PyRift prefers authoritative sources because CPython's
backwards-compatibility policy explicitly covers language behavior and public
API return values, side effects, and exceptions. PEP 387 says that an
incompatible behavior change normally goes through a deprecation process and
that a feature should not be removed between consecutive releases without
notice.

The normal evidence chain is therefore:

1. **PEP / official documentation** — establishes the documented contract and,
   when it describes a versioned behavior change, provides evidence that the
   change was deliberate.
2. **Deprecation path** — establishes that the old behavior was intentionally
   being phased out before removal or replacement.
3. **Runtime verification** — confirms that the claimed difference actually
   occurs on the relevant interpreter/version.
4. **Static detection** — finds code that relies on the affected behavior.

A runtime probe is deliberately not upgraded to `documented` merely because
it produces a stable result. That prevents PyRift from turning an accidental
implementation detail into a claim about CPython's design intent.

## Why this distinction matters

Python's reference documentation also warns that implementation details can
change and that different Python implementations may behave differently.
Consequently, a finding can be useful even when PyRift cannot establish that a
behavior change was intentional: code that depends on an undocumented or
implementation-specific behavior is still a portability/compatibility risk.

For example, CPY029 concerns `locals()` behavior that the rule explicitly
classifies as undefined behavior. It is therefore marked
`implementation_defined`, rather than claiming that CPython intentionally
changed a guaranteed language behavior.

## Maintainer-facing answer

If asked **"How does PyRift determine whether a behavior difference is
intentional?"**, the accurate answer is:

> PyRift does not infer intent from the runtime difference itself. It separates
> runtime evidence from intent evidence. For CPython version changes, it gives
> the strongest weight to PEPs, official documentation, and explicit
> deprecation/removal paths, and it reports runtime probes as confirmation of
> behavior rather than proof of maintainer intent. If the documented contract
> leaves behavior implementation-specific, PyRift marks that separately
> instead of calling the difference intentional.

## Authoritative references

- [PEP 387 — Backwards Compatibility Policy](https://peps.python.org/pep-0387/)
- [Python Language Reference — Introduction](https://docs.python.org/3/reference/introduction.html)
- [What's New in Python](https://docs.python.org/3/whatsnew/)
- [Python Deprecations](https://docs.python.org/3/deprecations/)
