from traffic_arena.engine import fixed_time_controller, run_scenario
from traffic_arena.scenarios import PUBLIC_SCENARIOS
from traffic_arena.scoring import scenario_score


def test_baseline_score_is_10000():
    result = run_scenario(PUBLIC_SCENARIOS[0], fixed_time_controller, record_replay=False)
    assert scenario_score(result.metrics.cost, result.metrics.cost) == 10_000


def test_replay_map_has_complete_streets_and_bounded_cars():
    scenario = PUBLIC_SCENARIOS[0]
    result = run_scenario(scenario, fixed_time_controller, record_replay=True)
    assert result.replay is not None
    assert len(result.replay["map"]["roads"]) == scenario.rows + scenario.cols
    assert all(
        -0.04 <= x <= 1.04 and -0.04 <= y <= 1.04
        for frame in result.replay["frames"]
        for _, x, y, _ in frame["vehicles"]
    )
