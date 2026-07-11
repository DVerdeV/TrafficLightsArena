from __future__ import annotations

import copy
import random
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from .scenarios import Scenario

GreenPhase = Literal["NS_GREEN", "EW_GREEN"]
Direction = Literal["N", "S", "E", "W"]
Controller = Callable[[dict[str, Any]], dict[str, GreenPhase]]


@dataclass(slots=True)
class Signal:
    phase: str = "NS_GREEN"
    phase_age: int = 0
    requested: GreenPhase = "NS_GREEN"
    next_phase: GreenPhase = "EW_GREEN"


@dataclass(slots=True)
class Vehicle:
    id: int
    direction: Direction
    route: tuple[str, ...]
    spawn_tick: int
    route_index: int = 0
    wait_ticks: int = 0
    travel_remaining: int = 0
    travel_total: int = 0
    from_intersection: str | None = None
    to_intersection: str | None = None
    finished_tick: int | None = None


@dataclass(frozen=True, slots=True)
class SimulationMetrics:
    spawned: int
    completed: int
    unfinished: int
    wait_ticks: int
    cost: int


@dataclass(frozen=True, slots=True)
class SimulationResult:
    scenario_id: str
    metrics: SimulationMetrics
    replay: dict[str, Any] | None


@dataclass(slots=True)
class _World:
    scenario: Scenario
    rng: random.Random
    signals: dict[str, Signal]
    queues: dict[str, dict[Direction, deque[int]]]
    vehicles: dict[int, Vehicle] = field(default_factory=dict)
    travelling: set[int] = field(default_factory=set)
    completed: set[int] = field(default_factory=set)
    next_vehicle_id: int = 1


MIN_GREEN = 5
YELLOW_TICKS = 2
ALL_RED_TICKS = 1
MAP_EDGE = 0.035
LANE_OFFSET_X = 0.012
LANE_OFFSET_Y = 0.021
STOP_DISTANCE_X = 0.046
STOP_DISTANCE_Y = 0.079
CAR_SPACING_X = 0.024
CAR_SPACING_Y = 0.041
ENTRY_TICKS = 5
EXIT_TICKS = 6
OFFSCREEN_X = 0.02
OFFSCREEN_Y = 0.035


def intersection_id(row: int, col: int) -> str:
    return f"{chr(65 + row)}{col + 1}"


def _make_world(scenario: Scenario) -> _World:
    ids = [intersection_id(row, col) for row in range(scenario.rows) for col in range(scenario.cols)]
    return _World(
        scenario=scenario,
        rng=random.Random(scenario.seed),
        signals={item: Signal() for item in ids},
        queues={item: {direction: deque() for direction in ("N", "S", "E", "W")} for item in ids},
    )


def _axis(direction: Direction) -> str:
    return "NS" if direction in ("N", "S") else "EW"


def _route_for(world: _World, direction: Direction, lane: int) -> tuple[str, ...]:
    scenario = world.scenario
    if direction == "E":
        return tuple(intersection_id(lane, col) for col in range(scenario.cols))
    if direction == "W":
        return tuple(intersection_id(lane, col) for col in reversed(range(scenario.cols)))
    if direction == "S":
        return tuple(intersection_id(row, lane) for row in range(scenario.rows))
    return tuple(intersection_id(row, lane) for row in reversed(range(scenario.rows)))


def _spawn_rate(scenario: Scenario, tick: int, axis: str) -> float:
    base = scenario.vertical_rate if axis == "NS" else scenario.horizontal_rate
    if scenario.rush_axis == axis:
        base *= 1.2 if tick < scenario.ticks * 0.6 else 0.75
    if scenario.burst_period and (tick // scenario.burst_period) % 2 == 0:
        base *= 1.45
    return min(base, 0.48)


def _spawn(world: _World, tick: int) -> None:
    scenario = world.scenario
    candidates: list[tuple[Direction, int]] = []
    candidates.extend((direction, row) for row in range(scenario.rows) for direction in ("E", "W"))
    candidates.extend((direction, col) for col in range(scenario.cols) for direction in ("N", "S"))
    for direction, lane in candidates:
        if world.rng.random() >= _spawn_rate(scenario, tick, _axis(direction)):
            continue
        route = _route_for(world, direction, lane)
        vehicle = Vehicle(world.next_vehicle_id, direction, route, tick)
        world.vehicles[vehicle.id] = vehicle
        world.queues[route[0]][direction].append(vehicle.id)
        world.next_vehicle_id += 1


def _queue_metrics(world: _World, intersection: str) -> tuple[dict[str, int], dict[str, int]]:
    sizes: dict[str, int] = {}
    oldest: dict[str, int] = {}
    for direction, queue in world.queues[intersection].items():
        sizes[direction] = len(queue)
        oldest[direction] = max((world.vehicles[vehicle_id].wait_ticks for vehicle_id in queue), default=0)
    return sizes, oldest


def _controller_state(world: _World, tick: int) -> dict[str, Any]:
    intersections: dict[str, Any] = {}
    for item, signal in world.signals.items():
        queues, oldest = _queue_metrics(world, item)
        intersections[item] = {
            "phase": signal.phase,
            "phase_age": signal.phase_age,
            "can_switch": signal.phase in ("NS_GREEN", "EW_GREEN") and signal.phase_age >= MIN_GREEN,
            "queues": queues,
            "oldest_wait": oldest,
        }

    links: dict[str, Any] = {}
    occupancy: dict[tuple[str, str], int] = defaultdict(int)
    for vehicle_id in world.travelling:
        vehicle = world.vehicles[vehicle_id]
        if vehicle.from_intersection and vehicle.to_intersection:
            occupancy[(vehicle.from_intersection, vehicle.to_intersection)] += 1
    for (source, target), count in occupancy.items():
        links[f"{source}->{target}"] = {
            "from": source,
            "to": target,
            "vehicles": count,
            "capacity": world.scenario.link_capacity,
        }

    return {
        "tick": tick,
        "remaining_ticks": world.scenario.ticks - tick,
        "map": {"rows": world.scenario.rows, "cols": world.scenario.cols},
        "intersections": intersections,
        "links": links,
        "vehicles": {
            "spawned": len(world.vehicles),
            "active": len(world.vehicles) - len(world.completed),
            "completed": len(world.completed),
        },
    }


def _apply_requests(world: _World, decisions: dict[str, GreenPhase]) -> None:
    if not isinstance(decisions, dict):
        raise TypeError("control(state) must return a dict")
    unknown = set(decisions) - set(world.signals)
    if unknown:
        raise ValueError(f"unknown intersection: {sorted(unknown)[0]}")
    for item, requested in decisions.items():
        if requested not in ("NS_GREEN", "EW_GREEN"):
            raise ValueError(f"invalid phase for {item}: {requested!r}")
        world.signals[item].requested = requested


def _advance_signals(world: _World) -> None:
    for signal in world.signals.values():
        if signal.phase in ("NS_GREEN", "EW_GREEN"):
            if signal.requested != signal.phase and signal.phase_age >= MIN_GREEN:
                signal.next_phase = signal.requested
                signal.phase = "YELLOW"
                signal.phase_age = 0
            else:
                signal.phase_age += 1
        elif signal.phase == "YELLOW":
            signal.phase_age += 1
            if signal.phase_age >= YELLOW_TICKS:
                signal.phase = "ALL_RED"
                signal.phase_age = 0
        else:
            signal.phase_age += 1
            if signal.phase_age >= ALL_RED_TICKS:
                signal.phase = signal.next_phase
                signal.phase_age = 0


def _link_occupancy(world: _World, source: str, target: str) -> int:
    return sum(
        1
        for vehicle_id in world.travelling
        if world.vehicles[vehicle_id].from_intersection == source
        and world.vehicles[vehicle_id].to_intersection == target
    )


def _release_queues(world: _World, tick: int) -> None:
    for item, by_direction in world.queues.items():
        phase = world.signals[item].phase
        for direction, queue in by_direction.items():
            if not queue or phase != f"{_axis(direction)}_GREEN":
                continue
            vehicle = world.vehicles[queue[0]]
            if tick - vehicle.spawn_tick < ENTRY_TICKS:
                continue
            if vehicle.route_index == len(vehicle.route) - 1:
                queue.popleft()
                vehicle.finished_tick = tick
                world.completed.add(vehicle.id)
                continue
            target = vehicle.route[vehicle.route_index + 1]
            if _link_occupancy(world, item, target) >= world.scenario.link_capacity:
                continue
            queue.popleft()
            vehicle.from_intersection = item
            vehicle.to_intersection = target
            vehicle.travel_total = world.scenario.travel_ticks
            vehicle.travel_remaining = world.scenario.travel_ticks
            world.travelling.add(vehicle.id)


def _advance_vehicles(world: _World) -> None:
    arrived: list[int] = []
    for vehicle_id in world.travelling:
        vehicle = world.vehicles[vehicle_id]
        vehicle.travel_remaining -= 1
        if vehicle.travel_remaining <= 0:
            arrived.append(vehicle_id)
    for vehicle_id in arrived:
        vehicle = world.vehicles[vehicle_id]
        world.travelling.remove(vehicle_id)
        vehicle.route_index += 1
        world.queues[vehicle.route[vehicle.route_index]][vehicle.direction].append(vehicle_id)
        vehicle.from_intersection = None
        vehicle.to_intersection = None


def _increment_wait(world: _World) -> None:
    for by_direction in world.queues.values():
        for queue in by_direction.values():
            for vehicle_id in queue:
                world.vehicles[vehicle_id].wait_ticks += 1


def _point(world: _World, intersection: str) -> tuple[float, float]:
    row = ord(intersection[0]) - 65
    col = int(intersection[1:]) - 1
    width = max(world.scenario.cols - 1, 1)
    height = max(world.scenario.rows - 1, 1)
    x_margin = 0.26 if world.scenario.cols == 2 else 0.16
    y_margin = 0.24 if world.scenario.rows == 2 else 0.15
    return (
        x_margin + (1 - 2 * x_margin) * col / width,
        y_margin + (1 - 2 * y_margin) * row / height,
    )


def _direction_vector(direction: Direction) -> tuple[int, int]:
    return {
        "E": (1, 0),
        "W": (-1, 0),
        "S": (0, 1),
        "N": (0, -1),
    }[direction]


def _lane_offset(direction: Direction) -> tuple[float, float]:
    dx, dy = _direction_vector(direction)
    return (-dy * LANE_OFFSET_X, dx * LANE_OFFSET_Y)


def _stop_distance(direction: Direction) -> float:
    return STOP_DISTANCE_X if direction in ("E", "W") else STOP_DISTANCE_Y


def _car_spacing(direction: Direction) -> float:
    return CAR_SPACING_X if direction in ("E", "W") else CAR_SPACING_Y


def _upstream_distance(world: _World, vehicle: Vehicle) -> float:
    current = vehicle.route[vehicle.route_index]
    x, y = _point(world, current)
    if vehicle.route_index > 0:
        px, py = _point(world, vehicle.route[vehicle.route_index - 1])
        return abs(x - px) + abs(y - py)
    if vehicle.direction == "E":
        return x - MAP_EDGE
    if vehicle.direction == "W":
        return 1 - MAP_EDGE - x
    if vehicle.direction == "S":
        return y - MAP_EDGE
    return 1 - MAP_EDGE - y


def _queue_spacing(world: _World, vehicle: Vehicle, queue_length: int) -> float:
    natural = _car_spacing(vehicle.direction)
    if queue_length <= 1:
        return natural
    usable = max(_upstream_distance(world, vehicle) - _stop_distance(vehicle.direction), natural)
    return min(natural, usable / (queue_length - 1))


def _queue_point(world: _World, vehicle: Vehicle, rank: int, queue_length: int) -> tuple[float, float]:
    current = vehicle.route[vehicle.route_index]
    x, y = _point(world, current)
    dx, dy = _direction_vector(vehicle.direction)
    lane_x, lane_y = _lane_offset(vehicle.direction)
    distance = _stop_distance(vehicle.direction) + rank * _queue_spacing(world, vehicle, queue_length)
    return (x - dx * distance + lane_x, y - dy * distance + lane_y)


def _boundary_point(world: _World, vehicle: Vehicle, *, entering: bool) -> tuple[float, float]:
    intersection = vehicle.route[0] if entering else vehicle.route[-1]
    x, y = _point(world, intersection)
    lane_x, lane_y = _lane_offset(vehicle.direction)
    if vehicle.direction == "E":
        return (-OFFSCREEN_X if entering else 1 + OFFSCREEN_X, y + lane_y)
    if vehicle.direction == "W":
        return (1 + OFFSCREEN_X if entering else -OFFSCREEN_X, y + lane_y)
    if vehicle.direction == "S":
        return (x + lane_x, -OFFSCREEN_Y if entering else 1 + OFFSCREEN_Y)
    return (x + lane_x, 1 + OFFSCREEN_Y if entering else -OFFSCREEN_Y)


def _vehicle_positions(world: _World, tick: int) -> list[list[Any]]:
    positions: list[list[Any]] = []
    queued_slots: dict[int, tuple[int, int]] = {}
    for by_direction in world.queues.values():
        for queue in by_direction.values():
            queued_slots.update(
                {vehicle_id: (index, len(queue)) for index, vehicle_id in enumerate(queue)}
            )

    headings = {"E": 0, "S": 90, "W": 180, "N": 270}
    for vehicle in world.vehicles.values():
        if vehicle.finished_tick is not None:
            exit_age = tick - vehicle.finished_tick
            if exit_age > EXIT_TICKS:
                continue
            start = _queue_point(world, vehicle, 0, 1)
            end = _boundary_point(world, vehicle, entering=False)
            progress = min(exit_age / EXIT_TICKS, 1)
            x = start[0] + (end[0] - start[0]) * progress
            y = start[1] + (end[1] - start[1]) * progress
        elif vehicle.id in world.travelling and vehicle.from_intersection and vehicle.to_intersection:
            dx, dy = _direction_vector(vehicle.direction)
            lane_x, lane_y = _lane_offset(vehicle.direction)
            stop_distance = _stop_distance(vehicle.direction)
            source_x, source_y = _point(world, vehicle.from_intersection)
            start = (
                source_x - dx * stop_distance + lane_x,
                source_y - dy * stop_distance + lane_y,
            )
            target_queue = world.queues[vehicle.to_intersection][vehicle.direction]
            target_rank = len(target_queue)
            target_length = target_rank + 1
            target_x, target_y = _point(world, vehicle.to_intersection)
            target_distance = stop_distance + target_rank * _queue_spacing(
                world, vehicle, target_length
            )
            end = (
                target_x - dx * target_distance + lane_x,
                target_y - dy * target_distance + lane_y,
            )
            progress = 1 - vehicle.travel_remaining / max(vehicle.travel_total, 1)
            x = start[0] + (end[0] - start[0]) * progress
            y = start[1] + (end[1] - start[1]) * progress
        else:
            rank, queue_length = queued_slots.get(vehicle.id, (0, 1))
            x, y = _queue_point(world, vehicle, rank, queue_length)
        entry_age = tick - vehicle.spawn_tick
        if entry_age < ENTRY_TICKS:
            entry_x, entry_y = _boundary_point(world, vehicle, entering=True)
            progress = entry_age / ENTRY_TICKS
            x = entry_x + (x - entry_x) * progress
            y = entry_y + (y - entry_y) * progress
        positions.append([vehicle.id, round(x, 4), round(y, 4), headings[vehicle.direction]])
    return positions


def _map_payload(world: _World) -> dict[str, Any]:
    intersections = []
    roads = []
    for row in range(world.scenario.rows):
        for col in range(world.scenario.cols):
            item = intersection_id(row, col)
            x, y = _point(world, item)
            intersections.append({"id": item, "x": x, "y": y})
    for row in range(world.scenario.rows):
        _, y = _point(world, intersection_id(row, 0))
        roads.append(
            {
                "from": f"west-{row}",
                "to": f"east-{row}",
                "x1": MAP_EDGE,
                "y1": y,
                "x2": 1 - MAP_EDGE,
                "y2": y,
            }
        )
    for col in range(world.scenario.cols):
        x, _ = _point(world, intersection_id(0, col))
        roads.append(
            {
                "from": f"north-{col}",
                "to": f"south-{col}",
                "x1": x,
                "y1": MAP_EDGE,
                "x2": x,
                "y2": 1 - MAP_EDGE,
            }
        )
    return {"rows": world.scenario.rows, "cols": world.scenario.cols, "intersections": intersections, "roads": roads}


def _frame(world: _World, tick: int) -> dict[str, Any]:
    return {
        "tick": tick,
        "vehicles": _vehicle_positions(world, tick),
        "signals": {item: signal.phase for item, signal in world.signals.items()},
        "completed": len(world.completed),
        "waiting": sum(vehicle.wait_ticks for vehicle in world.vehicles.values()),
    }


def run_scenario(scenario: Scenario, controller: Controller, *, record_replay: bool = True) -> SimulationResult:
    world = _make_world(scenario)
    frames: list[dict[str, Any]] = []

    for tick in range(scenario.ticks):
        _spawn(world, tick)
        decisions = controller(copy.deepcopy(_controller_state(world, tick)))
        _apply_requests(world, decisions)
        _advance_signals(world)
        _advance_vehicles(world)
        _release_queues(world, tick)
        _increment_wait(world)
        if record_replay:
            frames.append(_frame(world, tick))

    unfinished = len(world.vehicles) - len(world.completed)
    wait_ticks = sum(vehicle.wait_ticks for vehicle in world.vehicles.values())
    metrics = SimulationMetrics(
        spawned=len(world.vehicles),
        completed=len(world.completed),
        unfinished=unfinished,
        wait_ticks=wait_ticks,
        cost=wait_ticks + unfinished * 300,
    )
    replay = None
    if record_replay:
        replay = {
            "version": 1,
            "scenario": {"id": scenario.id, "name": scenario.name, "ticks": scenario.ticks},
            "map": _map_payload(world),
            "frames": frames,
            "metrics": {
                "spawned": metrics.spawned,
                "completed": metrics.completed,
                "unfinished": metrics.unfinished,
                "waitTicks": metrics.wait_ticks,
                "cost": metrics.cost,
            },
        }
    return SimulationResult(scenario.id, metrics, replay)


def fixed_time_controller(state: dict[str, Any]) -> dict[str, GreenPhase]:
    phase: GreenPhase = "NS_GREEN" if state["tick"] % 30 < 15 else "EW_GREEN"
    return {item: phase for item in state["intersections"]}
