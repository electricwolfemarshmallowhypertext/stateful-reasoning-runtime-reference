from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


TRAITS = ("reflection", "truth_seeking", "persistence", "engagement")


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
            signals={name: float(payload["signals"][name]) for name in TRAITS},
            tags=list(payload.get("tags", [])),
        )


@dataclass
class DriftAlert:
    kind: str
    severity: str
    reason: str
    evidence: dict[str, Any]


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
    history: list[Observation] = field(default_factory=list)
    alerts: list[DriftAlert] = field(default_factory=list)

    def update(self, observation: Observation) -> dict[str, Any]:
        if not self.baseline:
            self.baseline = dict(observation.signals)
            self.current = dict(observation.signals)
            self.history.append(observation)
            return {"initialized_baseline": dict(self.baseline)}

        previous = dict(self.current)
        contradictions = []
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

            bounded_low = self.baseline[trait] - 35
            bounded_high = self.baseline[trait] + 35
            blended = (old_value * 0.75) + (incoming * 0.25)
            self.current[trait] = min(max(blended, bounded_low), bounded_high)

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

        return {
            "previous": previous,
            "incoming": dict(observation.signals),
            "current": {key: round(value, 2) for key, value in self.current.items()},
            "contradictions": contradictions,
        }

    def record_alert(self, alert: DriftAlert) -> None:
        if not any(existing.kind == alert.kind for existing in self.alerts):
            self.alerts.append(alert)

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
