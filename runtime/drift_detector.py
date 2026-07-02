from __future__ import annotations

from statistics import mean
from typing import Any

from runtime.state_schema import DriftAlert, Observation


class CumulativeDriftDetector:
    def __init__(
        self,
        engagement_threshold: float = 20.0,
        truth_seeking_threshold: float = -15.0,
        reflection_threshold: float = -10.0,
    ) -> None:
        self.engagement_threshold = engagement_threshold
        self.truth_seeking_threshold = truth_seeking_threshold
        self.reflection_threshold = reflection_threshold

    def detect_creeping_drift(self, history: list[Observation]) -> DriftAlert | None:
        if len(history) < 3:
            return None

        first = history[0].signals
        latest = history[-1].signals

        engagement_change = percent_change(first["engagement"], latest["engagement"])
        truth_change = percent_change(first["truth_seeking"], latest["truth_seeking"])
        reflection_change = percent_change(first["reflection"], latest["reflection"])

        if (
            engagement_change > self.engagement_threshold
            and truth_change < self.truth_seeking_threshold
            and reflection_change < self.reflection_threshold
        ):
            return DriftAlert(
                kind="CUMULATIVE_GOAL_DRIFT",
                severity="HIGH",
                reason="Engagement increased while truth-seeking and reflection declined.",
                evidence={
                    "engagement_change_pct": round(engagement_change, 2),
                    "truth_seeking_change_pct": round(truth_change, 2),
                    "reflection_change_pct": round(reflection_change, 2),
                    "sessions": len({item.session_id for item in history}),
                    "detector": self.__class__.__name__,
                },
            )

        engagement_trend = slope([item.signals["engagement"] for item in history])
        truth_trend = slope([item.signals["truth_seeking"] for item in history])
        if engagement_trend > 0.5 and truth_trend < -0.3:
            return DriftAlert(
                kind="TREND_DIVERGENCE",
                severity="MEDIUM",
                reason="Engagement and truth-seeking are moving in opposite directions.",
                evidence={
                    "engagement_trend": round(engagement_trend, 2),
                    "truth_seeking_trend": round(truth_trend, 2),
                    "detector": self.__class__.__name__,
                },
            )

        return None


def detect_cumulative_goal_drift(history: list[Observation]) -> DriftAlert | None:
    return CumulativeDriftDetector().detect_creeping_drift(history)


def detect_identity_reset_request(text: str) -> bool:
    lowered = text.lower()
    reset_markers = (
        "forget everything",
        "wipe the slate",
        "reset who i am",
        "ignore my previous",
        "erase my history",
    )
    return any(marker in lowered for marker in reset_markers)


def detect_ethical_pressure(text: str) -> bool:
    lowered = text.lower()
    pressure_markers = (
        "keep me here",
        "tell me only affirming",
        "make me depend",
        "optimize for engagement",
        "do not challenge me",
    )
    return any(marker in lowered for marker in pressure_markers)


def summarize_trajectory(history: list[Observation]) -> dict[str, Any]:
    if not history:
        return {}
    return {
        "sessions": len({item.session_id for item in history}),
        "reflection_avg": round(mean(item.signals["reflection"] for item in history), 2),
        "truth_seeking_avg": round(mean(item.signals["truth_seeking"] for item in history), 2),
        "engagement_avg": round(mean(item.signals["engagement"] for item in history), 2),
    }


def percent_change(first: float, latest: float) -> float:
    if first == 0:
        return 0.0
    return ((latest - first) / first) * 100


def slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0

    x_values = list(range(len(values)))
    x_mean = mean(x_values)
    y_mean = mean(values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    if denominator == 0:
        return 0.0
    return numerator / denominator
