from __future__ import annotations

import math
from collections.abc import Sequence


def scenario_score(cost: int, baseline_cost: int) -> int:
    if baseline_cost <= 0:
        raise ValueError("baseline_cost must be positive")
    return min(25_000, round(10_000 * baseline_cost / max(cost, 1)))


def geometric_mean(scores: Sequence[int]) -> int:
    if not scores:
        raise ValueError("at least one score is required")
    if any(score <= 0 for score in scores):
        return 0
    return round(math.exp(sum(math.log(score) for score in scores) / len(scores)))


def aggregate_scores(public_scores: Sequence[int], hidden_scores: Sequence[int]) -> tuple[int, int, int]:
    public = geometric_mean(public_scores)
    hidden = geometric_mean(hidden_scores)
    return public, hidden, round(public * 0.4 + hidden * 0.6)
