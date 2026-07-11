import math

from traffic_arena.engine import fixed_time_controller, run_scenario
from traffic_arena.scenarios import PUBLIC_SCENARIOS
from traffic_arena.scoring import scenario_score


def test_baseline_score_is_10000():
    result = run_scenario(PUBLIC_SCENARIOS[0], fixed_time_controller, record_replay=False)
    assert scenario_score(result.metrics.cost, result.metrics.cost) == 10_000


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
