import math

import pytest

from traffic_arena.engine import _spawn_rate, fixed_time_controller, run_scenario
from traffic_arena.score_profiles import score_profile
from traffic_arena.scenarios import PUBLIC_SCENARIOS, DemandWindow, Scenario
from traffic_arena.scoring import aggregate_scores, scenario_score


def test_baseline_score_is_10000():
    result = run_scenario(PUBLIC_SCENARIOS[0], fixed_time_controller, record_replay=False)
    profile = score_profile(PUBLIC_SCENARIOS[0].id)
    assert scenario_score(result.metrics.cost, result.metrics.cost, profile.target_cost) == 10_000


def test_public_gold_targets_are_25000():
    for scenario in PUBLIC_SCENARIOS:
        profile = score_profile(scenario.id)
        assert scenario_score(profile.target_cost, profile.baseline_cost, profile.target_cost) == 25_000


def test_score_uses_squared_progress_and_20_80_aggregation():
    assert scenario_score(75, 100, 50) == 13_750
    assert scenario_score(25, 100, 50) == 25_000
    assert aggregate_scores([25_000], [10_000]) == (25_000, 10_000, 13_000)


def test_public_scenarios_keep_their_frozen_spawn_counts():
    for scenario in PUBLIC_SCENARIOS:
        result = run_scenario(scenario, fixed_time_controller, record_replay=False)
        assert result.metrics.spawned == score_profile(scenario.id).expected_spawned


def test_demand_windows_apply_direction_and_lane_weights():
    scenario = Scenario(
        "windowed",
        "Windowed demand",
        rows=2,
        cols=3,
        seed=7,
        ticks=4,
        demand_windows=(
            DemandWindow(0, 2, 0.1, 0.2, 0.3, 0.4, row_weights=(0.5, 2.0), col_weights=(1.0, 3.0, 5.0)),
            DemandWindow(2, 4, 0.05, 0.06, 0.07, 0.08),
        ),
    )

    assert _spawn_rate(scenario, 0, "E", 0) == pytest.approx(0.15)
    assert _spawn_rate(scenario, 0, "W", 1) == pytest.approx(0.48)
    assert _spawn_rate(scenario, 1, "N", 2) == pytest.approx(0.48)
    assert _spawn_rate(scenario, 1, "S", 1) == pytest.approx(0.48)
    assert _spawn_rate(scenario, 2, "E", 1) == pytest.approx(0.07)


@pytest.mark.parametrize(
    "windows",
    [
        (DemandWindow(1, 4, 0.1, 0.1, 0.1, 0.1),),
        (
            DemandWindow(0, 3, 0.1, 0.1, 0.1, 0.1),
            DemandWindow(2, 4, 0.1, 0.1, 0.1, 0.1),
        ),
        (DemandWindow(0, 3, 0.1, 0.1, 0.1, 0.1),),
    ],
)
def test_demand_windows_must_exactly_cover_scenario(windows):
    with pytest.raises(ValueError, match="cover"):
        Scenario("invalid", "Invalid", 2, 2, 1, ticks=4, demand_windows=windows)


def test_demand_window_weights_must_match_grid():
    window = DemandWindow(0, 4, 0.1, 0.1, 0.1, 0.1, row_weights=(1.0,), col_weights=(1.0, 1.0))
    with pytest.raises(ValueError, match="row_weights"):
        Scenario("invalid", "Invalid", 2, 2, 1, ticks=4, demand_windows=(window,))


def test_demand_window_values_must_be_nonnegative():
    with pytest.raises(ValueError, match="rates"):
        DemandWindow(0, 4, -0.1, 0.1, 0.1, 0.1)
    with pytest.raises(ValueError, match="weights"):
        DemandWindow(0, 4, 0.1, 0.1, 0.1, 0.1, row_weights=(-1.0,))


def test_replay_map_has_complete_streets_and_stable_traffic():
    scenario = PUBLIC_SCENARIOS[0]
    result = run_scenario(scenario, fixed_time_controller, record_replay=True)
    assert result.replay is not None
    assert len(result.replay["map"]["roads"]) == scenario.rows + scenario.cols
    previous = {}
    for frame in result.replay["frames"]:
        occupied = set()
        positions = []
        for vehicle_id, x, y, heading in frame["vehicles"]:
            position = (x, y)
            assert position not in occupied
            occupied.add(position)
            positions.append(position)
            if vehicle_id in previous:
                old_x, old_y, old_heading = previous[vehicle_id]
                radians = math.radians(old_heading)
                movement = (x - old_x) * 1200 * math.cos(radians) + (y - old_y) * 700 * math.sin(radians)
                assert movement >= -0.1
            previous[vehicle_id] = (x, y, heading)
        for index, first in enumerate(positions):
            for second in positions[index + 1:]:
                distance = math.hypot((first[0] - second[0]) * 1200, (first[1] - second[1]) * 700)
                assert distance >= 12
