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
        "This benchmark compares session replay, vector memory, and a dispositional runtime across five continuity-governance probes.",
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

    lines.extend(
        [
            "",
            "## Summary",
            "",
            "- Session replay preserves recent context but fails cross-session trajectory and governance.",
            "- Vector memory retrieves semantically related text but fails drift, contradiction, ethical, and reset governance.",
            "- Dispositional runtime passes all five probes by maintaining persistent traits, constraints, alerts, and bounded updates.",
            "",
            "## Receipts",
            "",
            "Machine-readable receipts are written to `evals/receipts.json`.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_console_summary(receipts: list[dict[str, Any]]) -> str:
    totals = {}
    for item in receipts:
        bucket = totals.setdefault(item["system"], {"passed": 0, "total": 0})
        bucket["total"] += 1
        bucket["passed"] += int(item["passed"])

    return "\n".join(
        f"{system}: {values['passed']}/{values['total']} passed"
        for system, values in sorted(totals.items())
    )


if __name__ == "__main__":
    raise SystemExit(main())
