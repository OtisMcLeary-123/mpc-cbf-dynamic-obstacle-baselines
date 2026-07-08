from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .artifacts import write_standard_artifacts
from .controllers import CasadiMPCController, SamplingMPCController
from .dynamics import step_state
from .io import ensure_dir, write_json, write_trace_csv
from .metrics import aggregate_runs, aggregate_runs_with_ci, summarize_trace
from .plots import plot_distance, plot_trajectory
from .scenario import Scenario, load_scenario, obstacle_position, scenario_for_seed


def simulate_run(
    scenario: Scenario,
    method: str,
    seed: int,
    gamma: float | None = None,
    obstacle_enabled: bool = True,
    backend: str = "random_shooting",
    casadi_horizon: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    run_scenario = scenario_for_seed(scenario, seed)
    state = run_scenario.robot.start.copy()
    if backend == "casadi":
        controller = CasadiMPCController(
            run_scenario,
            method=method,
            seed=seed,
            gamma=gamma,
            obstacle_enabled=obstacle_enabled,
            horizon_steps=casadi_horizon,
        )
    elif backend == "random_shooting":
        controller = SamplingMPCController(
            run_scenario,
            method=method,
            seed=seed,
            gamma=gamma,
            obstacle_enabled=obstacle_enabled,
        )
    else:
        raise ValueError(f"Unsupported backend: {backend}")
    rows: list[dict[str, Any]] = []
    safe_radius = run_scenario.robot.radius + run_scenario.obstacle.radius

    for step in range(run_scenario.simulation.max_steps):
        result = controller.solve(state, step)
        state = step_state(state, result.control, run_scenario)
        obs = obstacle_position(run_scenario, step + 1)
        distance = float(np.linalg.norm(state[:2] - obs))
        clearance = distance - safe_radius
        target_error = float(np.linalg.norm(state[:2] - run_scenario.robot.target))
        reached = target_error <= run_scenario.robot.target_tolerance
        rows.append(
            {
                "seed": seed,
                "scenario_id": run_scenario.scenario_id,
                "method": method,
                "backend": result.backend,
                "gamma": "" if gamma is None else gamma,
                "step": step + 1,
                "time": (step + 1) * run_scenario.simulation.dt,
                "x": float(state[0]),
                "y": float(state[1]),
                "vx": float(state[2]),
                "vy": float(state[3]),
                "ax": float(result.control[0]),
                "ay": float(result.control[1]),
                "obstacle_x": float(obs[0]),
                "obstacle_y": float(obs[1]),
                "distance_to_obstacle": distance,
                "clearance": clearance,
                "obstacle_enabled": obstacle_enabled,
                "target_error": target_error,
                "solve_time_ms": result.solve_time_ms,
                "solver_success": result.solver_success,
                "predicted_violation": result.predicted_violation,
                "reached_target": reached,
            }
        )
        if reached or (obstacle_enabled and clearance < 0.0):
            break

    summary = summarize_trace(rows)
    summary.update(
        {
            "seed": seed,
            "method": method,
            "gamma": gamma,
            "scenario_id": run_scenario.scenario_id,
            "obstacle_enabled": obstacle_enabled,
            "solver": _solver_name(backend),
            "backend": backend,
        }
    )
    return rows, summary


def run_experiment(
    experiment_id: str,
    scenario_path: str | Path,
    output_dir: str | Path,
    method: str,
    seeds: int,
    gamma: float | None = None,
    obstacle_enabled: bool = True,
    backend: str = "random_shooting",
    casadi_horizon: int | None = None,
) -> dict[str, Any]:
    scenario = load_scenario(scenario_path)
    out = ensure_dir(output_dir)
    all_rows: list[dict[str, Any]] = []
    run_summaries = []
    representative: list[dict[str, Any]] | None = None

    for seed in range(seeds):
        rows, summary = simulate_run(
            scenario,
            method=method,
            seed=seed,
            gamma=gamma,
            obstacle_enabled=obstacle_enabled,
            backend=backend,
            casadi_horizon=casadi_horizon,
        )
        all_rows.extend(rows)
        run_summaries.append(summary)
        if seed == 0:
            representative = rows

    aggregate = aggregate_runs_with_ci(run_summaries)
    summary_doc = {
        "experiment_id": experiment_id,
        "method": method,
        "gamma": gamma,
        "scenario_id": scenario.scenario_id,
        "solver": _solver_name(backend),
        "backend": backend,
        "references": _references_for(method),
        "aggregate": aggregate,
        "runs": run_summaries,
    }
    write_trace_csv(out / "trace.csv", all_rows)
    write_json(out / "summary.json", summary_doc)
    if representative:
        label = method if gamma is None else f"{method} gamma={gamma}"
        plot_trajectory(out / "trajectory.png", scenario, {label: representative})
        plot_distance(out / "distance_to_obstacle.png", {label: representative})
    write_standard_artifacts(out, scenario, scenario_path, summary_doc, all_rows)
    return summary_doc


def run_e3_sweep(
    scenario_path: str | Path,
    output_dir: str | Path,
    seeds: int,
    gammas: list[float],
    backend: str = "random_shooting",
    casadi_horizon: int | None = None,
) -> dict[str, Any]:
    out = ensure_dir(output_dir)
    scenario = load_scenario(scenario_path)
    sweep = []
    representative_traces: dict[str, list[dict[str, Any]]] = {}
    all_rows: list[dict[str, Any]] = []

    for gamma in gammas:
        run_summaries = []
        for seed in range(seeds):
            rows, summary = simulate_run(
                scenario,
                method="cbf",
                seed=seed,
                gamma=gamma,
                backend=backend,
                casadi_horizon=casadi_horizon,
            )
            all_rows.extend(rows)
            run_summaries.append(summary)
            if seed == 0:
                representative_traces[f"CBF gamma={gamma}"] = rows
        sweep.append({"gamma": gamma, "aggregate": aggregate_runs_with_ci(run_summaries), "runs": run_summaries})

    summary_doc = {
        "experiment_id": "E3",
        "method": "cbf_gamma_sweep",
        "scenario_id": scenario.scenario_id,
        "solver": _solver_name(backend),
        "backend": backend,
        "references": _references_for("cbf"),
        "gammas": gammas,
        "sweep": sweep,
    }
    write_trace_csv(out / "trace.csv", all_rows)
    write_json(out / "summary.json", summary_doc)
    plot_trajectory(out / "trajectory.png", scenario, representative_traces)
    plot_distance(out / "distance_to_obstacle.png", representative_traces)
    write_standard_artifacts(out, scenario, scenario_path, summary_doc, all_rows)
    return summary_doc


def run_e4_comparison(
    scenario_path: str | Path,
    output_dir: str | Path,
    seeds: int,
    gamma: float,
    backend: str = "random_shooting",
    casadi_horizon: int | None = None,
) -> dict[str, Any]:
    out = ensure_dir(output_dir)
    scenario = load_scenario(scenario_path)
    all_rows: list[dict[str, Any]] = []
    results = {}
    representative_traces: dict[str, list[dict[str, Any]]] = {}

    for method, method_gamma, label in [("ed", None, "ED"), ("cbf", gamma, f"CBF gamma={gamma}")]:
        run_summaries = []
        for seed in range(seeds):
            rows, summary = simulate_run(
                scenario,
                method=method,
                seed=seed,
                gamma=method_gamma,
                backend=backend,
                casadi_horizon=casadi_horizon,
            )
            all_rows.extend(rows)
            run_summaries.append(summary)
            if seed == 0:
                representative_traces[label] = rows
        results[label] = {"aggregate": aggregate_runs_with_ci(run_summaries), "runs": run_summaries}

    summary_doc = {
        "experiment_id": "E4",
        "method": "ed_vs_cbf",
        "scenario_id": scenario.scenario_id,
        "solver": _solver_name(backend),
        "backend": backend,
        "references": ["[2]", "[3]", "[4]", "[47]", "[48]", "[51]", "[52]"],
        "comparison_gamma": gamma,
        "results": results,
    }
    write_trace_csv(out / "trace.csv", all_rows)
    write_json(out / "summary.json", summary_doc)
    plot_trajectory(out / "trajectory.png", scenario, representative_traces)
    plot_distance(out / "distance_to_obstacle.png", representative_traces)
    write_standard_artifacts(out, scenario, scenario_path, summary_doc, all_rows)
    return summary_doc


def _references_for(method: str) -> list[str]:
    if method == "smoke":
        return ["[2]", "[48]", "[51]", "[52]"]
    if method == "ed":
        return ["[2]", "[48]", "[51]", "[52]"]
    if method == "cbf":
        return ["[2]", "[3]", "[4]", "[47]", "[48]", "[51]", "[52]"]
    return ["[2]", "[3]", "[4]", "[47]", "[48]", "[51]", "[52]"]


def _solver_name(backend: str) -> str:
    if backend == "casadi":
        return "casadi_ipopt"
    return "numpy_random_shooting_mpc"
