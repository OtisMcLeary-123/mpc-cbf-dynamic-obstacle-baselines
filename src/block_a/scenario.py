from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class RobotConfig:
    start: np.ndarray
    target: np.ndarray
    radius: float
    max_speed: float
    max_accel: float
    target_tolerance: float


@dataclass(frozen=True)
class ObstacleConfig:
    radius: float
    initial_position: np.ndarray
    velocity: np.ndarray


@dataclass(frozen=True)
class SimulationConfig:
    dt: float
    horizon_steps: int
    max_steps: int
    dev_seeds: int
    paper_seeds: int
    candidate_sequences: int
    seed_obstacle_position_std: np.ndarray
    seed_obstacle_velocity_std: np.ndarray
    obstacle_prediction_noise_std: np.ndarray


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    robot: RobotConfig
    obstacle: ObstacleConfig
    simulation: SimulationConfig
    metrics: list[str]


def load_scenario(path: str | Path) -> Scenario:
    data = json.loads(Path(path).read_text())
    robot = data["robot"]
    obstacle = data["obstacle"]
    simulation = data["simulation"]
    return Scenario(
        scenario_id=data["scenario_id"],
        robot=RobotConfig(
            start=np.array(robot["start"], dtype=float),
            target=np.array(robot["target"], dtype=float),
            radius=float(robot.get("radius", 0.12)),
            max_speed=float(robot.get("max_speed", 1.4)),
            max_accel=float(robot.get("max_accel", 2.2)),
            target_tolerance=float(robot.get("target_tolerance", 0.18)),
        ),
        obstacle=ObstacleConfig(
            radius=float(obstacle["radius"]),
            initial_position=np.array(obstacle["initial_position"], dtype=float),
            velocity=np.array(obstacle["velocity"], dtype=float),
        ),
        simulation=SimulationConfig(
            dt=float(simulation["dt"]),
            horizon_steps=int(simulation["horizon_steps"]),
            max_steps=int(simulation["max_steps"]),
            dev_seeds=int(simulation["dev_seeds"]),
            paper_seeds=int(simulation["paper_seeds"]),
            candidate_sequences=int(simulation.get("candidate_sequences", 384)),
            seed_obstacle_position_std=np.array(
                simulation.get("seed_obstacle_position_std", [0.0, 0.0]), dtype=float
            ),
            seed_obstacle_velocity_std=np.array(
                simulation.get("seed_obstacle_velocity_std", [0.0, 0.0]), dtype=float
            ),
            obstacle_prediction_noise_std=np.array(
                simulation.get("obstacle_prediction_noise_std", [0.0, 0.0]), dtype=float
            ),
        ),
        metrics=list(data.get("metrics", [])),
    )


def scenario_for_seed(scenario: Scenario, seed: int) -> Scenario:
    rng = np.random.default_rng(seed)
    obstacle = replace(
        scenario.obstacle,
        initial_position=scenario.obstacle.initial_position
        + rng.normal(0.0, scenario.simulation.seed_obstacle_position_std),
        velocity=scenario.obstacle.velocity
        + rng.normal(0.0, scenario.simulation.seed_obstacle_velocity_std),
    )
    return replace(scenario, obstacle=obstacle)


def obstacle_position(scenario: Scenario, step: int | np.ndarray) -> np.ndarray:
    step_array = np.asarray(step, dtype=float)
    time = step_array[..., None] * scenario.simulation.dt
    return scenario.obstacle.initial_position + time * scenario.obstacle.velocity


def predicted_obstacle_position(
    scenario: Scenario, step: int | np.ndarray, seed: int = 0
) -> np.ndarray:
    position = obstacle_position(scenario, step)
    std = scenario.simulation.obstacle_prediction_noise_std
    if not np.any(std):
        return position
    step_array = np.asarray(step, dtype=int)
    rng = np.random.default_rng(seed * 100_003 + int(np.max(step_array)) * 1009 + 17)
    return position + rng.normal(0.0, std, size=position.shape)
