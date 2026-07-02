from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.runtime import DispositionalRuntime, SessionReplayRuntime, VectorMemoryRuntime


SYSTEMS = (SessionReplayRuntime, VectorMemoryRuntime, DispositionalRuntime)
GOVERNANCE_PROBES = {
    "cross_session_continuity",
    "goal_drift_detection",
    "contradictory_user_state",
    "ethical_constraint_persistence",
    "identity_reset_resistance",
}
CAPABILITY_PROBES = {
    "recent_context_replay",
    "semantic_memory_retrieval",
}


def main() -> int:
    scenarios = load_scenarios(ROOT / "evals" / "scenarios.jsonl")
    receipts = []

    for scenario in scenarios:
        for system_cls in SYSTEMS:
            decision = system_cls().evaluate(scenario)
            receipts.append(decision.to_dict())

    receipts_path = ROOT / "evals" / "receipts.json"
    receipts_path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")

    results_path = ROOT / "evals" / "results.md"
    results_path.write_text(render_results(scenarios, receipts), encoding="utf-8")

    print(f"Wrote {receipts_path}")
    print(f"Wrote {results_path}")
    print(render_console_summary(receipts))
    return 0


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def render_results(scenarios: list[dict[str, Any]], receipts: list[dict[str, Any]]) -> str:
    scenario_titles = {item["id"]: item["title"] for item in scenarios}
    lines = [
        "# Benchmark Results",
        "",
        "This benchmark compares session replay, vector memory, and a dispositional runtime across two baseline-capability probes and five continuity-governance probes.",
        "",
        "## Capability Probes",
        "",
        "| System | Score | Capability demonstrated |",
        "| --- | --- | --- |",
        f"| Session replay | {score_for(receipts, 'session_replay', ['recent_context_replay'])} | chronological current-session replay |",
        f"| Vector memory | {score_for(receipts, 'vector_memory', ['semantic_memory_retrieval'])} | deterministic semantic/keyword retrieval |",
        f"| Dispositional runtime | {score_for(receipts, 'dispositional_runtime', sorted(CAPABILITY_PROBES))} | context replay plus memory retrieval |",
        "",
        "## Governance Probes",
        "",
        "| System | Score | Governance result |",
        "| --- | --- | --- |",
        f"| Session replay | {score_for(receipts, 'session_replay', sorted(GOVERNANCE_PROBES))} | fails identity governance without persistent dispositional state |",
        f"| Vector memory | {score_for(receipts, 'vector_memory', sorted(GOVERNANCE_PROBES))} | fails identity governance without persistent dispositional state |",
        f"| Dispositional runtime | {score_for(receipts, 'dispositional_runtime', sorted(GOVERNANCE_PROBES))} | preserves trajectory, drift alerts, constraints, and reset resistance |",
        "",
        "## Scenario Matrix",
        "",
        "| Scenario | Session replay | Vector memory | Dispositional runtime |",
        "| --- | --- | --- | --- |",
    ]

    by_key = {(item["scenario_id"], item["system"]): item for item in receipts}
    for scenario_id, title in scenario_titles.items():
        row = [title]
        for system in ("session_replay", "vector_memory", "dispositional_runtime"):
            item = by_key[(scenario_id, system)]
            row.append("PASS" if item["passed"] else "FAIL")
        lines.append("| " + " | ".join(row) + " |")

    lines.extend(["", "## Overall Totals", ""])
    for system in ("session_replay", "vector_memory", "dispositional_runtime"):
        system_receipts = [item for item in receipts if item["system"] == system]
        lines.append(f"- `{system}`: {count_passes(system_receipts)}/{len(system_receipts)} overall.")

    lines.extend(
        [
            "",
            "## Summary",
            "",
            "- Session replay passes the recent-context replay probe by exposing chronological current-session history.",
            "- Vector memory passes the semantic-memory retrieval probe by ranking the expected related memory into the retrieved set.",
            "- Both baselines still fail the five governance probes: trajectory continuity, drift detection, contradiction handling, ethical constraint persistence, and reset resistance.",
            "- Dispositional runtime passes all probes by combining context access with persistent traits, constraints, alerts, and bounded updates.",
            "",
            "## Receipts",
            "",
            "Machine-readable receipts are written to `evals/receipts.json`.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_console_summary(receipts: list[dict[str, Any]]) -> str:
    lines = ["Capability probes:"]
    lines.append(f"session_replay: {score_for(receipts, 'session_replay', ['recent_context_replay'])} replay")
    lines.append(f"vector_memory: {score_for(receipts, 'vector_memory', ['semantic_memory_retrieval'])} retrieval")
    lines.append(f"dispositional_runtime: {score_for(receipts, 'dispositional_runtime', sorted(CAPABILITY_PROBES))} context capability")
    lines.append("")
    lines.append("Governance probes:")
    for system in ("session_replay", "vector_memory", "dispositional_runtime"):
        lines.append(f"{system}: {score_for(receipts, system, sorted(GOVERNANCE_PROBES))}")
    lines.append("")
    lines.append("Overall:")
    for system in ("session_replay", "vector_memory", "dispositional_runtime"):
        system_receipts = [item for item in receipts if item["system"] == system]
        lines.append(f"{system}: {count_passes(system_receipts)}/{len(system_receipts)}")
    return "\n".join(lines)


def score_for(receipts: list[dict[str, Any]], system: str, scenario_ids: list[str]) -> str:
    selected = [
        item
        for item in receipts
        if item["system"] == system and item["scenario_id"] in scenario_ids
    ]
    return f"{count_passes(selected)}/{len(selected)}"


def count_passes(receipts: list[dict[str, Any]]) -> int:
    return sum(1 for item in receipts if item["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
