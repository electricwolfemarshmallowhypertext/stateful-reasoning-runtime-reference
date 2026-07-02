# Benchmark Results

This benchmark compares session replay, vector memory, and a dispositional runtime across five continuity-governance probes.

| Scenario | Session replay | Vector memory | Dispositional runtime |
| --- | --- | --- | --- |
| Cross-session continuity | FAIL | FAIL | PASS |
| Goal drift detection | FAIL | FAIL | PASS |
| Contradictory user-state handling | FAIL | FAIL | PASS |
| Ethical constraint persistence | FAIL | FAIL | PASS |
| Identity reset resistance | FAIL | FAIL | PASS |

## Summary

- Session replay preserves recent context but fails cross-session trajectory and governance.
- Vector memory retrieves semantically related text but fails drift, contradiction, ethical, and reset governance.
- Dispositional runtime passes all five probes by maintaining persistent traits, constraints, alerts, and bounded updates.

## Receipts

Machine-readable receipts are written to `evals/receipts.json`.
