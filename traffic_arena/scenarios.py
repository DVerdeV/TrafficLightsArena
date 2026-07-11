from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    name: str
    rows: int
    cols: int
    seed: int
    ticks: int = 900
    travel_ticks: int = 5
    link_capacity: int = 8
    horizontal_rate: float = 0.13
    vertical_rate: float = 0.13
    rush_axis: str | None = None
    burst_period: int = 0


PUBLIC_SCENARIOS = (
    Scenario("balanced-grid", "Balanced grid", 2, 2, 1403),
    Scenario(
        "northbound-morning",
        "Northbound morning",
        3,
        2,
        8191,
        vertical_rate=0.22,
        horizontal_rate=0.09,
        rush_axis="NS",
    ),
    Scenario(
        "city-rush",
        "City rush",
        3,
        3,
        27183,
        horizontal_rate=0.17,
        vertical_rate=0.17,
        burst_period=90,
    ),
)
