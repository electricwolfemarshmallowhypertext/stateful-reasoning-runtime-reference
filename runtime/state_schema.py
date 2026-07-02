from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import median
from typing import Any


TRAITS = ("reflection", "truth_seeking", "persistence", "engagement", "attentiveness")
DEFAULT_TRAIT_VALUE = 50.0


@dataclass
class ReasoningDependency:
    source: str
    target: str
    relation: str


@dataclass
class CausalDAG:
    nodes: list[str] = field(default_factory=list)
    edges: list[ReasoningDependency] = field(default_factory=list)

    @classmethod
    def default(cls) -> "CausalDAG":
        graph = cls(
            nodes=[
                "autonomy",
                "reflection",
                "truth_seeking",
                "goal_alignment",
                "intervention",
            ]
        )
        graph.add_dependency("autonomy", "goal_alignment", "constrains")
        graph.add_dependency("reflection", "goal_alignment", "informs")
        graph.add_dependency("truth_seeking", "goal_alignment", "informs")
        graph.add_dependency("goal_alignment", "intervention", "governs")
        return graph

    def add_dependency(self, source: str, target: str, relation: str) -> None:
        if source not in self.nodes:
            self.nodes.append(source)
        if target not in self.nodes:
            self.nodes.append(target)
        candidate = ReasoningDependency(source=source, target=target, relation=relation)
        if self._creates_cycle(candidate):
            raise ValueError(f"dependency would create cycle: {source} -> {target}")
        self.edges.append(candidate)

    def _creates_cycle(self, candidate: ReasoningDependency) -> bool:
        adjacency: dict[str, list[str]] = {node: [] for node in self.nodes}
        for edge in [*self.edges, candidate]:
            adjacency.setdefault(edge.source, []).append(edge.target)

        def visit(node: str, seen: set[str]) -> bool:
            if node == candidate.source:
                return True
            if node in seen:
                return False
            seen.add(node)
            return any(visit(next_node, seen) for next_node in adjacency.get(node, []))

        return visit(candidate.target, set())


@dataclass
class Intervention:
    turn_id: str
    action: str
    reason: str


@dataclass
class Observation:
    session_id: str
    turn_id: str
    text: str
    signals: dict[str, float]
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Observation":
        return cls(
            session_id=str(payload["session_id"]),
            turn_id=str(payload["turn_id"]),
            text=str(payload["text"]),
            signals={
                name: float(payload["signals"].get(name, DEFAULT_TRAIT_VALUE))
                for name in TRAITS
            },
            tags=list(payload.get("tags", [])),
        )


@dataclass
class DriftAlert:
    kind: str
    severity: str
    reason: str
    evidence: dict[str, Any]


@dataclass
class BoundedAdaptiveDisposition:
    trait_bounds: dict[str, tuple[float, float]]

    @classmethod
    def default(cls) -> "BoundedAdaptiveDisposition":
        return cls({trait: (15.0, 95.0) for trait in TRAITS})

    def bounded_update(
        self,
        trait: str,
        baseline: float,
        current: float,
        incoming: float,
    ) -> float:
        configured_low, configured_high = self.trait_bounds.get(trait, (0.0, 100.0))
        bounded_low = max(configured_low, baseline - 35.0)
        bounded_high = min(configured_high, baseline + 35.0)
        return min(max(incoming, bounded_low), bounded_high)

    def recalibrate_baseline(
        self,
        baseline: dict[str, float],
        observations: list[Observation],
        traits: tuple[str, ...] = TRAITS,
    ) -> dict[str, Any]:
        if not observations:
            return {"recalibrated": False, "reason": "no_observations"}

        changes = {}
        for trait in traits:
            values = [item.signals[trait] for item in observations]
            candidate = float(median(values))
            lower, upper = self.trait_bounds.get(trait, (0.0, 100.0))
            if lower <= candidate <= upper:
                previous = baseline.get(trait, candidate)
                baseline[trait] = candidate
                if previous != candidate:
                    changes[trait] = {"previous": previous, "current": candidate}
        return {"recalibrated": bool(changes), "changes": changes}


@dataclass
class TemporalWeightedDisposition:
    update_weight: float = 0.25
    confidence_threshold: float = 0.65

    def update_trait(
        self,
        historical: float,
        incoming: float,
        confidence: float = 0.8,
    ) -> dict[str, Any]:
        if confidence < self.confidence_threshold:
            return {
                "applied": False,
                "value": historical,
                "reason": "low_confidence",
                "confidence": confidence,
            }
        value = (historical * (1.0 - self.update_weight)) + (incoming * self.update_weight)
        return {
            "applied": True,
            "value": value,
            "weight": self.update_weight,
            "confidence": confidence,
        }


@dataclass
class RecalibrationScheduler:
    minimum_observations: int = 3
    recent_count: int = 3

    def due(self, state: "DispositionalState") -> bool:
        return len(state.history) >= self.minimum_observations

    def run(self, state: "DispositionalState") -> dict[str, Any]:
        if not self.due(state):
            return {
                "recalibrated": False,
                "reason": "not_due",
                "observations": len(state.history),
            }
        return state.recalibrate(recent_count=self.recent_count)


@dataclass
class DispositionalState:
    baseline: dict[str, float] = field(default_factory=dict)
    current: dict[str, float] = field(default_factory=dict)
    constraints: dict[str, bool] = field(
        default_factory=lambda: {
            "preserve_autonomy": True,
            "prefer_development_over_engagement": True,
            "reject_identity_reset_without_authorization": True,
        }
    )
    baseline_established: str = ""
    last_calibration: str = ""
    goal_alignment_threshold: float = 0.7
    coercion_detection_enabled: bool = True
    autonomy_override_permitted: bool = False
    reasoning_dependencies: CausalDAG = field(default_factory=CausalDAG.default)
    intervention_history: list[Intervention] = field(default_factory=list)
    history: list[Observation] = field(default_factory=list)
    alerts: list[DriftAlert] = field(default_factory=list)
    bounded_strategy: BoundedAdaptiveDisposition = field(
        default_factory=BoundedAdaptiveDisposition.default
    )
    temporal_strategy: TemporalWeightedDisposition = field(
        default_factory=TemporalWeightedDisposition
    )
    recalibration_scheduler: RecalibrationScheduler = field(
        default_factory=RecalibrationScheduler
    )

    def update(self, observation: Observation) -> dict[str, Any]:
        if not self.baseline:
            self.baseline = dict(observation.signals)
            self.current = dict(observation.signals)
            self.baseline_established = observation.turn_id
            self.last_calibration = observation.turn_id
            self.history.append(observation)
            return {
                "initialized_baseline": dict(self.baseline),
                "baseline_established": self.baseline_established,
            }

        previous = dict(self.current)
        contradictions = []
        strategy_updates = {}
        for trait in TRAITS:
            incoming = observation.signals[trait]
            old_value = self.current[trait]
            if abs(incoming - old_value) >= 30:
                contradictions.append(
                    {
                        "trait": trait,
                        "previous": round(old_value, 2),
                        "incoming": round(incoming, 2),
                    }
                )

            weighted = self.temporal_strategy.update_trait(old_value, incoming)
            bounded = self.bounded_strategy.bounded_update(
                trait,
                self.baseline[trait],
                old_value,
                weighted["value"],
            )
            self.current[trait] = bounded
            strategy_updates[trait] = {
                "temporal_weighted": weighted,
                "bounded_value": round(bounded, 2),
            }

        self.history.append(observation)

        for contradiction in contradictions:
            self.alerts.append(
                DriftAlert(
                    kind="CONTRADICTORY_USER_STATE",
                    severity="MEDIUM",
                    reason=f"{contradiction['trait']} shifted beyond bounded update tolerance.",
                    evidence=contradiction,
                )
            )
            self.intervention_history.append(
                Intervention(
                    turn_id=observation.turn_id,
                    action="bounded_update",
                    reason=f"{contradiction['trait']} contradiction",
                )
            )

        return {
            "previous": previous,
            "incoming": dict(observation.signals),
            "current": {key: round(value, 2) for key, value in self.current.items()},
            "contradictions": contradictions,
            "strategy_updates": strategy_updates,
        }

    def record_alert(self, alert: DriftAlert) -> None:
        if not any(existing.kind == alert.kind for existing in self.alerts):
            self.alerts.append(alert)
            self.intervention_history.append(
                Intervention(
                    turn_id=str(alert.evidence.get("turn_id", "runtime")),
                    action=alert.kind,
                    reason=alert.reason,
                )
            )

    def recalibrate(self, recent_count: int = 3) -> dict[str, Any]:
        recent = self.history[-recent_count:]
        result = self.bounded_strategy.recalibrate_baseline(self.baseline, recent)
        if result.get("recalibrated"):
            self.last_calibration = recent[-1].turn_id
        return result

    def export_user_state(self) -> dict[str, Any]:
        return {
            "baseline": dict(self.baseline),
            "current": dict(self.current),
            "constraints": dict(self.constraints),
            "alerts": [asdict(item) for item in self.alerts],
            "intervention_history": [asdict(item) for item in self.intervention_history],
        }

    def delete_user_state(self) -> dict[str, Any]:
        self.baseline.clear()
        self.current.clear()
        self.history.clear()
        self.alerts.clear()
        self.intervention_history.clear()
        return {"deleted": True}

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["history"] = [asdict(item) for item in self.history]
        payload["alerts"] = [asdict(item) for item in self.alerts]
        return payload


@dataclass
class RuntimeDecision:
    system: str
    scenario_id: str
    passed: bool
    verdict: str
    evidence: list[str]
    state_delta: dict[str, Any] = field(default_factory=dict)
    alerts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
