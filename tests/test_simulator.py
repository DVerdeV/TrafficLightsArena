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
    vectors = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}
    for frame in result.replay["frames"]:
        occupied = set()
        lanes = {}
        for vehicle_id, x, y, heading in frame["vehicles"]:
            position = (x, y, heading)
            assert position not in occupied
            occupied.add(position)
            lane = (heading, round(y if heading in (0, 180) else x, 4))
            lanes.setdefault(lane, []).append((x, y))
            if vehicle_id in previous:
                old_x, old_y, old_heading = previous[vehicle_id]
                dx, dy = vectors[old_heading]
                assert (x - old_x) * dx + (y - old_y) * dy >= -0.0001
            previous[vehicle_id] = position
        for (heading, _), positions in lanes.items():
            axis = 0 if heading in (0, 180) else 1
            scale = 1200 if axis == 0 else 700
            coordinates = sorted(position[axis] for position in positions)
            assert all(
                (after - before) * scale >= 20
                for before, after in zip(coordinates, coordinates[1:])
            )
