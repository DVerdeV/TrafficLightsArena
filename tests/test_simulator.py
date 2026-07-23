import math

from traffic_arena.engine import fixed_time_controller, run_scenario
from traffic_arena.scenarios import PUBLIC_SCENARIOS, Scenario
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


def test_signal_transition_is_green_yellow_red_green():
    scenario = Scenario("transition-test", "Transition test", 1, 1, 12, ticks=12, horizontal_rate=0, vertical_rate=0)

    def request_east_west(state):
        return {item: "EW_GREEN" for item in state["intersections"]}

    replay = run_scenario(scenario, request_east_west, record_replay=True).replay
    assert replay is not None
    assert replay["version"] == 2
    phases = [frame["signals"]["A1"] for frame in replay["frames"]]
    assert ["NS_YELLOW", "NS_YELLOW", "ALL_RED", "EW_GREEN"] in [
        phases[index:index + 4] for index in range(len(phases) - 3)
    ]


def test_stopped_cars_are_behind_the_stop_bars():
    scenario = Scenario(
        "stop-test",
        "Stop test",
        1,
        1,
        31,
        ticks=35,
        horizontal_rate=0.48,
        vertical_rate=0,
    )
    replay = run_scenario(scenario, lambda state: {item: "NS_GREEN" for item in state["intersections"]}).replay
    assert replay is not None
    intersection_x = replay["map"]["intersections"][0]["x"]
    west_bar_x = intersection_x - 50 / 1200
    east_bar_x = intersection_x + 50 / 1200
    for frame in replay["frames"][10:]:
        for _vehicle_id, x, _y, heading in frame["vehicles"]:
            if heading == 0:
                assert x + 13 / 1200 <= west_bar_x
            elif heading == 180:
                assert x - 13 / 1200 >= east_bar_x
