# Stateful Reasoning Runtime Reference

Reference implementation for evaluating dispositional state as a governance layer over stateless LLM calls.

## License

This repository is released under the Business Source License 1.1.

The code is source-available for non-production research, evaluation, education, and personal experimentation. Production use, hosted service use, resale, sublicensing, or use to provide commercial AI governance/runtime services requires a separate commercial license.

On July 2, 2030, the license converts to Apache License 2.0.

## This repository accompanies:

**Stateful Reasoning Runtimes V2: Architectural Patterns for Identity Persistence Over Stateless LLM APIs**

It provides a minimal deterministic benchmark comparing three architectural patterns for state management in LLM applications:

1. **Session replay** - preserves recent chronological context.
2. **Vector memory** - retrieves related historical records through deterministic memory search.
3. **Dispositional runtime** - maintains persistent governance state, including traits, constraints, drift alerts, and reset resistance.

The purpose of this repository is not to build a production agent framework. It is a small proof artifact for testing a specific architectural claim:

> Stateless model calls plus memory retrieval do not produce identity continuity. Identity continuity requires a persistent dispositional governance layer.

## Reference Implementation

The implementation separates three kinds of state:

| Layer | Function |
|---|---|
| Conversational state | Recent session context and chronological replay |
| Associative state | Persistent memory retrieval over prior records |
| Dispositional state | Persistent governance constraints, behavioral continuity, and drift detection |

The LLM call remains stateless. Continuity is supplied by the runtime layer before and after the call.

Implemented components include:

```txt
SessionReplayRuntime
VectorMemoryRuntime
DispositionalRuntime
BoundedAdaptiveDisposition
TemporalWeightedDisposition
CumulativeDriftDetector
RecalibrationScheduler
StatelessPromptAssembler
InMemoryVectorIndex
LocalEncryptedStateStore
CausalDAG
```

`LocalEncryptedStateStore` is a local/offline reference implementation for the proof artifact. It is not production cryptography.

## Benchmark

The benchmark evaluates capability probes separately from governance probes.

### Capability probes

```txt
session_replay: 1/1 replay
vector_memory: 1/1 retrieval
dispositional_runtime: 2/2 context capability
```

### Governance probes

```txt
session_replay: 0/5
vector_memory: 0/5
dispositional_runtime: 5/5
```

### Overall

```txt
session_replay: 1/7
vector_memory: 1/7
dispositional_runtime: 7/7
```

The result is intentionally narrow. It does not claim general intelligence, clinical validity, therapeutic efficacy, or complete identity preservation. It demonstrates that replay and memory can preserve context, but they do not provide persistent governance without an explicit dispositional state layer.

## Run

```bash
python evals/run_eval.py
python evals/verify_architecture.py
```

The benchmark is deterministic and does not require an external model, embedding API, or network access.
`evals/verify_architecture.py` exercises the named architecture components directly.

## Outputs

```txt
evals/receipts.json
evals/results.md
```

`receipts.json` contains machine-readable evidence for state updates, replay context, memory retrieval scores, and governance decisions.

`results.md` contains the human-readable benchmark summary.

## Repository Structure

```txt
runtime/
  state_schema.py
  drift_detector.py
  privacy.py
  prompting.py
  runtime.py
  vector_index.py

evals/
  scenarios.jsonl
  run_eval.py
  verify_architecture.py
  receipts.json
  results.md

paper/
  stateful_reasoning_runtimes_v2.md
```

## Citation

Reference implementation release:

```txt
https://github.com/electricwolfemarshmallowhypertext/stateful-reasoning-runtime-reference/releases/tag/v0.3.0
```

Paper DOI:

```txt
10.5281/zenodo.17755157
```

## Scope

This repository is a research artifact. It is designed to make the architectural distinction testable:

```txt
Replay is not governance.
Memory is not governance.
Dispositional state is governance.
```
