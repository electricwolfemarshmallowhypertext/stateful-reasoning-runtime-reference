This repo demonstrates dispositional state as a governance layer over stateless LLM calls.

## Run

```bash
python evals/run_eval.py
```

The benchmark compares three systems:

- `session_replay`: recent session context only.
- `vector_memory`: persistent semantic recall without governance.
- `dispositional_runtime`: persistent traits, constraints, drift alerts, and reset resistance.

Outputs:

- `evals/receipts.json`: machine-readable state updates and decisions.
- `evals/results.md`: human-readable benchmark summary.

## Claim Under Test

Stateless model plus memory retrieval is not identity continuity. Identity continuity requires a dispositional governance layer.
