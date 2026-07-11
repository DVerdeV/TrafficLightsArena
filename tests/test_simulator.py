from traffic_arena.engine import fixed_time_controller, run_scenario
from traffic_arena.scenarios import PUBLIC_SCENARIOS
from traffic_arena.scoring import scenario_score


def test_baseline_score_is_10000():
    result = run_scenario(PUBLIC_SCENARIOS[0], fixed_time_controller, record_replay=False)
    assert scenario_score(result.metrics.cost, result.metrics.cost) == 10_000
