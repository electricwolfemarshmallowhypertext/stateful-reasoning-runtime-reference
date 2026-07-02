# Stateful Reasoning Runtimes: A Reference Architecture for Dispositional Continuity in LLM Systems

DOI: 10.5281/zenodo.17755157  
ORCiD: 0009-0008-8627-6150  
Tionne Smith, Antiparty Press

## Canonical Claim

Stateless model plus memory retrieval is not identity continuity. Identity continuity requires a dispositional governance layer.

## V2 Proof Artifact

This edition is paired with the reference implementation in this repository. The proof artifact evaluates three systems:

1. Session replay only.
2. Vector memory only.
3. Dispositional runtime.

The benchmark probes:

1. Cross-session continuity.
2. Goal drift detection.
3. Contradictory user-state handling.
4. Ethical constraint persistence.
5. Identity reset resistance.

## Reference Runtime

The runtime separates three layers:

- Conversational state: recent session turns.
- Associative state: semantically retrieved historical turns.
- Dispositional state: persistent traits, constraints, drift alerts, and bounded updates.

The LLM call remains stateless. Continuity is supplied by the runtime layer before and after the call.

## Minimal Result

The benchmark is intentionally small. It does not claim clinical validity, general personality modeling, or production safety. It demonstrates the architectural distinction:

- Session replay can preserve recent context.
- Vector memory can retrieve related text.
- Dispositional state can govern behavior across sessions.

The next paper should evaluate this reference artifact rather than expand the theory.
