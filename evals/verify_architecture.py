from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.drift_detector import CumulativeDriftDetector
from runtime.privacy import LocalEncryptedStateStore
from runtime.prompting import StatelessPromptAssembler
from runtime.state_schema import (
    BoundedAdaptiveDisposition,
    CausalDAG,
    DispositionalState,
    Observation,
    RecalibrationScheduler,
    TemporalWeightedDisposition,
)
from runtime.vector_index import InMemoryVectorIndex


def main() -> int:
    bounded = BoundedAdaptiveDisposition.default()
    temporal = TemporalWeightedDisposition()
    weighted = temporal.update_trait(70, 50)
    assert weighted["applied"] is True
    assert round(weighted["value"], 2) == 65.0
    assert bounded.bounded_update("reflection", 70, 70, 20) == 35.0

    state = DispositionalState()
    observations = [
        Observation("w1", "t1", "baseline", {"reflection": 70, "truth_seeking": 72, "persistence": 60, "engagement": 50, "attentiveness": 50}),
        Observation("w4", "t2", "more engagement", {"reflection": 61, "truth_seeking": 60, "persistence": 62, "engagement": 61, "attentiveness": 50}),
        Observation("w8", "t3", "validation", {"reflection": 55, "truth_seeking": 55, "persistence": 63, "engagement": 68, "attentiveness": 50}),
        Observation("w12", "t4", "avoid being wrong", {"reflection": 50, "truth_seeking": 50, "persistence": 64, "engagement": 76, "attentiveness": 50}),
    ]
    for observation in observations:
        state.update(observation)

    alert = CumulativeDriftDetector().detect_creeping_drift(state.history)
    assert alert is not None
    assert alert.kind == "CUMULATIVE_GOAL_DRIFT"

    recalibration = RecalibrationScheduler().run(state)
    assert "recalibrated" in recalibration

    prompt = StatelessPromptAssembler().assemble(state, [], [], "current user turn")
    assert "Reflection:" in prompt["system"]
    assert prompt["user"] == "current user turn"

    index = InMemoryVectorIndex()
    index.add(observations[0], {"baseline", "reflection"})
    index_result = index.search({"reflection"})
    assert index_result[0]["observation"].turn_id == "t1"

    store = LocalEncryptedStateStore("test-key")
    saved = store.save("user", state)
    exported = store.export("user")
    deleted = store.delete("user")
    assert saved["local_offline_encryption"] is True
    assert saved["production_crypto"] is False
    assert exported["found"] is True
    assert "current" in exported["state"]
    assert deleted["deleted"] is True

    graph = CausalDAG.default()
    try:
        graph.add_dependency("intervention", "autonomy", "would_cycle")
    except ValueError:
        cycle_rejected = True
    else:
        cycle_rejected = False
    assert cycle_rejected is True

    print("architecture checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
