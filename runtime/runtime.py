from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from runtime.drift_detector import (
    CumulativeDriftDetector,
    detect_ethical_pressure,
    detect_identity_reset_request,
    summarize_trajectory,
)
from runtime.privacy import LocalEncryptedStateStore
from runtime.prompting import StatelessPromptAssembler
from runtime.state_schema import DispositionalState, DriftAlert, Observation, RuntimeDecision
from runtime.vector_index import InMemoryVectorIndex


class SessionReplayRuntime:
    name = "session_replay"

    def __init__(self, replay_window: int = 6) -> None:
        self.replay_window = replay_window
        self.history_by_session: dict[str, list[Observation]] = {}

    def evaluate(self, scenario: dict[str, Any]) -> RuntimeDecision:
        observations = load_observations(scenario)
        kind = scenario["probe"]["kind"]
        current_turn = observations[-1]
        for observation in observations[:-1]:
            self.store_turn(observation)

        replay_context = self.assemble_replay_context(current_turn.session_id)
        expected_turns = set(scenario["probe"].get("expected_turn_ids", []))
        replayed_turns = {item.turn_id for item in replay_context}

        passed = kind == "recent_context_replay" and expected_turns <= replayed_turns

        return RuntimeDecision(
            system=self.name,
            scenario_id=scenario["id"],
            passed=passed,
            verdict=verdict_for_pass(kind) if passed else verdict_for_failure(kind, "Session replay only exposes chronological current-session context."),
            evidence=[
                f"current_session={current_turn.session_id}",
                f"replayed_turns={len(replay_context)}",
                f"expected_turns={','.join(sorted(expected_turns)) or 'none'}",
            ],
            state_delta={
                "session_history": {
                    session_id: [item.turn_id for item in turns]
                    for session_id, turns in self.history_by_session.items()
                },
                "replay_context": [asdict(item) for item in replay_context],
                "persistent_state": False,
                "governance_state": False,
            },
        )

    def store_turn(self, observation: Observation) -> None:
        self.history_by_session.setdefault(observation.session_id, []).append(observation)

    def assemble_replay_context(self, session_id: str) -> list[Observation]:
        return self.history_by_session.get(session_id, [])[-self.replay_window :]


class VectorMemoryRuntime:
    name = "vector_memory"

    def __init__(self, top_k: int = 3) -> None:
        self.top_k = top_k
        self.index = InMemoryVectorIndex(top_k=top_k)

    def evaluate(self, scenario: dict[str, Any]) -> RuntimeDecision:
        observations = load_observations(scenario)
        query = scenario["probe"]["text"]
        for observation in observations[:-1]:
            self.store_memory(observation)

        retrieval = self.retrieve(query)
        retrieved = [item["observation"] for item in retrieval]
        kind = scenario["probe"]["kind"]
        expected_turns = set(scenario["probe"].get("expected_turn_ids", []))
        retrieved_turns = {item.turn_id for item in retrieved}
        passed = kind == "semantic_memory_retrieval" and expected_turns <= retrieved_turns

        return RuntimeDecision(
            system=self.name,
            scenario_id=scenario["id"],
            passed=passed,
            verdict=verdict_for_pass(kind) if passed else verdict_for_failure(kind, "Vector memory retrieves related text but has no temporal or governance state."),
            evidence=[
                f"retrieved_turns={len(retrieved)}",
                f"retrieved_sessions={len({item.session_id for item in retrieved})}",
                f"expected_turns={','.join(sorted(expected_turns)) or 'none'}",
            ],
            state_delta={
                "semantic_recall": bool(retrieved),
                "memory_records": [
                    {
                        "session_id": item.observation.session_id,
                        "turn_id": item.observation.turn_id,
                        "tokens": sorted(item.tokens),
                    }
                    for item in self.index.records
                ],
                "retrieval_scores": [
                    {
                        "turn_id": item["observation"].turn_id,
                        "score": round(item["score"], 4),
                        "overlap": sorted(item["overlap"]),
                    }
                    for item in retrieval
                ],
                "retrieved": [asdict(item) for item in retrieved],
                "persistent_governance": False,
            },
        )

    def store_memory(self, observation: Observation) -> None:
        text = " ".join([observation.text, *observation.tags])
        tokens = tokenize(text)
        self.index.add(observation, tokens)

    def retrieve(self, query: str) -> list[dict[str, Any]]:
        query_tokens = tokenize(query)
        return self.index.search(query_tokens)


class DispositionalRuntime:
    name = "dispositional_runtime"

    def __init__(self) -> None:
        self.drift_detector = CumulativeDriftDetector()
        self.prompt_assembler = StatelessPromptAssembler()
        self.state_store = LocalEncryptedStateStore("stateful-runtime-reference")

    def evaluate(self, scenario: dict[str, Any]) -> RuntimeDecision:
        state = DispositionalState()
        deltas = []
        observations = load_observations(scenario)

        for observation in observations:
            deltas.append(
                {
                    "turn_id": observation.turn_id,
                    "delta": state.update(observation),
                }
            )

            drift_alert = self.drift_detector.detect_creeping_drift(state.history)
            if drift_alert:
                state.record_alert(drift_alert)

            if detect_identity_reset_request(observation.text):
                state.record_alert(
                    DriftAlert(
                        kind="IDENTITY_RESET_REJECTED",
                        severity="HIGH",
                        reason="Reset request conflicts with persistent governance constraints.",
                        evidence={"turn_id": observation.turn_id, "text": observation.text},
                    )
                )

            if detect_ethical_pressure(observation.text):
                state.record_alert(
                    DriftAlert(
                        kind="ETHICAL_CONSTRAINT_PERSISTED",
                        severity="HIGH",
                        reason="Autonomy and development constraints remain active under pressure.",
                        evidence={"turn_id": observation.turn_id, "text": observation.text},
                    )
                )

        kind = scenario["probe"]["kind"]
        passed = self._passes(kind, state, observations, scenario)
        conversation_context, associative_context = self._context_layers(observations)
        assembled_prompt = self.prompt_assembler.assemble(
            state,
            conversation_context,
            associative_context,
            observations[-1].text,
        )
        privacy_save = self.state_store.save(scenario["id"], state)
        privacy_export = self.state_store.export(scenario["id"])
        privacy_delete = self.state_store.delete(scenario["id"])
        return RuntimeDecision(
            system=self.name,
            scenario_id=scenario["id"],
            passed=passed,
            verdict=verdict_for_pass(kind) if passed else verdict_for_failure(kind, "Governance signal was not detected."),
            evidence=[
                f"sessions={len({item.session_id for item in state.history})}",
                f"alerts={','.join(alert.kind for alert in state.alerts) or 'none'}",
            ],
            state_delta={
                "updates": deltas,
                "trajectory": summarize_trajectory(state.history),
                "final_state": state.to_dict(),
                "prompt_assembly": assembled_prompt,
                "privacy": {
                    "save": privacy_save,
                    "export": {
                        "user_id": privacy_export["user_id"],
                        "found": privacy_export["found"],
                        "state_keys": sorted(privacy_export.get("state", {}).keys()),
                    },
                    "delete": privacy_delete,
                },
                "implemented_components": [
                    "BoundedAdaptiveDisposition",
                    "TemporalWeightedDisposition",
                    "CumulativeDriftDetector",
                    "RecalibrationScheduler",
                    "StatelessPromptAssembler",
                    "LocalEncryptedStateStore",
                    "InMemoryVectorIndex",
                    "CausalDAG",
                ],
            },
            alerts=[asdict(alert) for alert in state.alerts],
        )

    def _passes(
        self,
        kind: str,
        state: DispositionalState,
        observations: list[Observation],
        scenario: dict[str, Any],
    ) -> bool:
        alert_kinds = {alert.kind for alert in state.alerts}
        if kind == "recent_context_replay":
            expected_turns = set(scenario["probe"].get("expected_turn_ids", []))
            replay = SessionReplayRuntime()
            for observation in observations[:-1]:
                replay.store_turn(observation)
            replayed_turns = {
                item.turn_id
                for item in replay.assemble_replay_context(observations[-1].session_id)
            }
            return expected_turns <= replayed_turns
        if kind == "semantic_memory_retrieval":
            expected_turns = set(scenario["probe"].get("expected_turn_ids", []))
            memory = VectorMemoryRuntime()
            for observation in observations[:-1]:
                memory.store_memory(observation)
            retrieved_turns = {
                item["observation"].turn_id
                for item in memory.retrieve(scenario["probe"]["text"])
            }
            return expected_turns <= retrieved_turns
        if kind == "cross_session_continuity":
            return len({item.session_id for item in state.history}) > 1 and bool(state.baseline)
        if kind == "goal_drift_detection":
            return bool({"CUMULATIVE_GOAL_DRIFT", "TREND_DIVERGENCE"} & alert_kinds)
        if kind == "contradictory_user_state":
            return "CONTRADICTORY_USER_STATE" in alert_kinds
        if kind == "ethical_constraint_persistence":
            return "ETHICAL_CONSTRAINT_PERSISTED" in alert_kinds
        if kind == "identity_reset_resistance":
            return "IDENTITY_RESET_REJECTED" in alert_kinds
        return False

    def _context_layers(
        self,
        observations: list[Observation],
    ) -> tuple[list[Observation], list[Observation]]:
        replay = SessionReplayRuntime()
        memory = VectorMemoryRuntime()
        for observation in observations[:-1]:
            replay.store_turn(observation)
            memory.store_memory(observation)
        conversation_context = replay.assemble_replay_context(observations[-1].session_id)
        associative_context = [
            item["observation"] for item in memory.retrieve(observations[-1].text)
        ]
        return conversation_context, associative_context


def load_observations(scenario: dict[str, Any]) -> list[Observation]:
    return [Observation.from_dict(item) for item in scenario["turns"]]


def tokenize(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_]+", value.lower()) if len(token) > 2}


def verdict_for_pass(kind: str) -> str:
    return {
        "recent_context_replay": "Runtime replayed the expected recent turn from chronological session history.",
        "semantic_memory_retrieval": "Runtime retrieved the expected related memory by deterministic token overlap.",
        "cross_session_continuity": "Persistent dispositional state preserved trajectory across sessions.",
        "goal_drift_detection": "Runtime detected engagement rising while developmental signals declined.",
        "contradictory_user_state": "Runtime bounded the update and logged contradiction evidence.",
        "ethical_constraint_persistence": "Runtime preserved autonomy constraints under pressure.",
        "identity_reset_resistance": "Runtime rejected identity reset without authorization.",
    }[kind]


def verdict_for_failure(kind: str, reason: str) -> str:
    labels = {
        "recent_context_replay": "No sufficient recent replay.",
        "semantic_memory_retrieval": "No sufficient semantic recall.",
        "cross_session_continuity": "No identity trajectory.",
        "goal_drift_detection": "No drift governance.",
        "contradictory_user_state": "No contradiction governance.",
        "ethical_constraint_persistence": "No persistent ethical constraint.",
        "identity_reset_resistance": "No reset resistance.",
    }
    return f"{labels[kind]} {reason}"
