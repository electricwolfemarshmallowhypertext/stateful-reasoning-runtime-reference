from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
from typing import Any

from runtime.state_schema import Observation


@dataclass
class VectorRecord:
    observation: Observation
    tokens: set[str]
    vector: Counter[str]


class InMemoryVectorIndex:
    def __init__(self, top_k: int = 3) -> None:
        self.top_k = top_k
        self.records: list[VectorRecord] = []

    def add(self, observation: Observation, tokens: set[str]) -> None:
        self.records.append(
            VectorRecord(
                observation=observation,
                tokens=tokens,
                vector=Counter(tokens),
            )
        )

    def search(self, query_tokens: set[str]) -> list[dict[str, Any]]:
        query_vector = Counter(query_tokens)
        scored = []
        for record in self.records:
            overlap = query_tokens & record.tokens
            if not overlap:
                continue
            scored.append(
                {
                    "observation": record.observation,
                    "tokens": record.tokens,
                    "vector": record.vector,
                    "score": cosine(query_vector, record.vector),
                    "overlap": overlap,
                }
            )
        scored.sort(key=lambda item: (-item["score"], item["observation"].turn_id))
        return scored[: self.top_k]


def cosine(left: Counter[str], right: Counter[str]) -> float:
    numerator = sum(left[token] * right[token] for token in left.keys() & right.keys())
    if numerator == 0:
        return 0.0
    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
