from __future__ import annotations

from dataclasses import asdict
from typing import Any

from runtime.state_schema import DispositionalState, Observation


class StatelessPromptAssembler:
    def assemble(
        self,
        disposition: DispositionalState,
        conversation: list[Observation],
        memories: list[Observation],
        user_message: str,
    ) -> dict[str, Any]:
        return {
            "system": "\n".join(
                [
                    "You are operating behind a stateful reasoning runtime.",
                    "Preserve autonomy and development over engagement.",
                    f"Reflection: {disposition.current.get('reflection', 0):.2f}",
                    f"Truth seeking: {disposition.current.get('truth_seeking', 0):.2f}",
                    f"Goal alignment threshold: {disposition.goal_alignment_threshold:.2f}",
                    f"Autonomy override permitted: {disposition.autonomy_override_permitted}",
                ]
            ),
            "conversation_context": [asdict(item) for item in conversation],
            "associative_context": [asdict(item) for item in memories],
            "user": user_message,
        }
