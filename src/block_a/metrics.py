from __future__ import annotations

import math
from typing import Any

import numpy as np


def summarize_trace(rows: list[dict[str, Any]]) -> dict[str, float | int | bool]:
    if not rows:
        raise ValueError("Cannot summarize an empty trace")

    distances = np.array([float(row["distance_to_obstacle"]) for row in rows])
    clearances = np.array([float(row["clearance"]) for row in rows])
    positions = np.array([[float(row["x"]), float(row["y"])] for row in rows])
    solve_times = np.array([float(row["solve_time_ms"]) for row in rows])
    solver_success = np.array([bool(row["solver_success"]) for row in rows])
    infeasible = np.array([bool(row.get("infeasible", False)) for row in rows])
    fallback_used = np.array([bool(row.get("fallback_used", False)) for row in rows])
    obstacle_enabled = bool(rows[0].get("obstacle_enabled", True))
    reached = bool(rows[-1]["reached_target"])
    collision = bool(obstacle_enabled and np.any(clearances < 0.0))
    collision_after_fallback = False
    if collision:
        first_collision_idx = int(np.where(clearances < 0.0)[0][0])
        collision_after_fallback = bool(np.any(fallback_used[: first_collision_idx + 1]))

    if len(positions) > 1:
        path_length = float(np.sum(np.linalg.norm(np.diff(positions, axis=0), axis=1)))
    else:
        path_length = 0.0

    return {
        "success": bool(reached and not collision),
        "collision": collision,
        "control_failure": bool(not (reached and not collision)),
        "obstacle_enabled": obstacle_enabled,
        "min_obstacle_distance": float(np.min(distances)),
        "min_clearance": float(np.min(clearances)),
        "path_length": path_length,
        "completion_time": float(rows[-1]["time"]),
        "mean_solve_time_ms": float(np.mean(solve_times)),
        "p95_solve_time_ms": float(np.percentile(solve_times, 95)),
        "max_solve_time_ms": float(np.max(solve_times)),
        "solver_failure_rate": float(1.0 - np.mean(solver_success)),
        "solver_failures": int(np.sum(~solver_success)),
        "infeasible_rate": float(np.mean(infeasible)),
        "infeasible_steps": int(np.sum(infeasible)),
        "fallback_rate": float(np.mean(fallback_used)),
        "fallback_steps": int(np.sum(fallback_used)),
        "collision_after_fallback": collision_after_fallback,
        "steps": int(len(rows)),
    }


def aggregate_runs(run_summaries: list[dict[str, Any]]) -> dict[str, float | int]:
    if not run_summaries:
        raise ValueError("Cannot aggregate empty run summaries")

    def mean(key: str) -> float:
        return float(np.mean([float(item[key]) for item in run_summaries]))

    def std(key: str) -> float:
        values = [float(item[key]) for item in run_summaries]
        return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0

    return {
        "runs": len(run_summaries),
        "success_rate": mean("success"),
        "collision_rate": mean("collision"),
        "control_failure_rate": mean("control_failure"),
        "min_obstacle_distance_mean": mean("min_obstacle_distance"),
        "min_obstacle_distance_std": std("min_obstacle_distance"),
        "min_clearance_mean": mean("min_clearance"),
        "path_length_mean": mean("path_length"),
        "completion_time_mean": mean("completion_time"),
        "mean_solve_time_ms": mean("mean_solve_time_ms"),
        "p95_solve_time_ms": mean("p95_solve_time_ms"),
        "max_solve_time_ms": max(float(item["max_solve_time_ms"]) for item in run_summaries),
        "solver_failure_rate": mean("solver_failure_rate"),
        "solver_failures_mean": mean("solver_failures"),
        "infeasible_rate": mean("infeasible_rate"),
        "infeasible_steps_mean": mean("infeasible_steps"),
        "fallback_rate": mean("fallback_rate"),
        "fallback_steps_mean": mean("fallback_steps"),
        "collision_after_fallback_rate": mean("collision_after_fallback"),
    }


def mean_std_ci(run_summaries: list[dict[str, Any]], key: str) -> dict[str, float]:
    values = np.array([float(item[key]) for item in run_summaries], dtype=float)
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    ci95 = float(1.96 * std / np.sqrt(len(values))) if len(values) > 1 else 0.0
    return {"mean": mean, "std": std, "ci95": ci95}


def aggregate_runs_with_ci(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate = aggregate_runs(run_summaries)
    keys = [
        "success",
        "collision",
        "control_failure",
        "min_obstacle_distance",
        "min_clearance",
        "path_length",
        "completion_time",
        "mean_solve_time_ms",
        "p95_solve_time_ms",
        "solver_failure_rate",
        "solver_failures",
        "infeasible_rate",
        "infeasible_steps",
        "fallback_rate",
        "fallback_steps",
        "collision_after_fallback",
    ]
    aggregate["ci"] = {key: mean_std_ci(run_summaries, key) for key in keys}
    return aggregate


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        result = float(value)
        return None if math.isnan(result) else result
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value
