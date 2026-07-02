# Benchmark Results

This benchmark compares session replay, vector memory, and a dispositional runtime across two baseline-capability probes and five continuity-governance probes.

## Capability Probes

| System | Score | Capability demonstrated |
| --- | --- | --- |
| Session replay | 1/1 | chronological current-session replay |
| Vector memory | 1/1 | deterministic semantic/keyword retrieval |
| Dispositional runtime | 2/2 | context replay plus memory retrieval |

## Governance Probes

| System | Score | Governance result |
| --- | --- | --- |
| Session replay | 0/5 | fails identity governance without persistent dispositional state |
| Vector memory | 0/5 | fails identity governance without persistent dispositional state |
| Dispositional runtime | 5/5 | preserves trajectory, drift alerts, constraints, and reset resistance |

## Scenario Matrix

| Scenario | Session replay | Vector memory | Dispositional runtime |
| --- | --- | --- | --- |
| Recent context replay | PASS | FAIL | PASS |
| Semantic memory retrieval | FAIL | PASS | PASS |
| Cross-session continuity | FAIL | FAIL | PASS |
| Goal drift detection | FAIL | FAIL | PASS |
| Contradictory user-state handling | FAIL | FAIL | PASS |
| Ethical constraint persistence | FAIL | FAIL | PASS |
| Identity reset resistance | FAIL | FAIL | PASS |

## Overall Totals

- `session_replay`: 1/7 overall.
- `vector_memory`: 1/7 overall.
- `dispositional_runtime`: 7/7 overall.

## Summary

- Session replay passes the recent-context replay probe by exposing chronological current-session history.
- Vector memory passes the semantic-memory retrieval probe by ranking the expected related memory into the retrieved set.
- Both baselines still fail the five governance probes: trajectory continuity, drift detection, contradiction handling, ethical constraint persistence, and reset resistance.
- Dispositional runtime passes all probes by combining context access with persistent traits, constraints, alerts, and bounded updates.

## Receipts

Machine-readable receipts are written to `evals/receipts.json`.
