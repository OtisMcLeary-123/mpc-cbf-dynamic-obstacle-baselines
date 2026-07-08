from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from .io import ensure_dir, write_csv, write_trace_csv
from .metrics import json_ready
from .plots import plot_distance, plot_metric_boxplot, plot_trajectory
from .scenario import Scenario


SCHEMA_VERSION = "lampc_block_artifacts_v1"


def write_standard_artifacts(
    output_dir: str | Path,
    scenario: Scenario,
    scenario_path: str | Path,
    summary_doc: dict[str, Any],
    trace_rows: list[dict[str, Any]],
) -> None:
    out = ensure_dir(output_dir)
    ensure_dir(out / "trajectories")
    ensure_dir(out / "figures")
    ensure_dir(out / "logs")

    seed_labels = _seed_zero_traces(trace_rows)
    write_config_yaml(out / "config.yaml", scenario_path, summary_doc)
    write_metrics_summary_csv(out / "metrics_summary.csv", summary_doc)
    write_per_seed_metrics_csv(out / "per_seed_metrics.csv", summary_doc)
    write_trajectory_files(out / "trajectories", trace_rows)
    write_standard_figures(out / "figures", scenario, seed_labels, summary_doc)
    write_report(out / "report.md", summary_doc)
    write_run_log(out / "logs/run.log", summary_doc, trace_rows)


def write_config_yaml(path: str | Path, scenario_path: str | Path, summary_doc: dict[str, Any]) -> None:
    method_labels = [row["label"] for row in _summary_rows(summary_doc)]
    lines = [
        f"schema_version: {SCHEMA_VERSION}",
        "block: A",
        f"experiment_name: {Path(path).parent.name}",
        f"experiment_id: {summary_doc.get('experiment_id', '')}",
        f"scenario_id: {summary_doc.get('scenario_id', '')}",
        f"scenario_path: {Path(scenario_path)}",
        f"backend: {summary_doc.get('backend', '')}",
        f"solver: {summary_doc.get('solver', '')}",
        f"generated_at_utc: {datetime.now(timezone.utc).isoformat()}",
        "methods:",
        *[f"  - {label}" for label in method_labels],
        "references:",
        *[f"  - \"{ref}\"" for ref in summary_doc.get("references", [])],
    ]
    if "comparison_gamma" in summary_doc:
        lines.append(f"comparison_gamma: {summary_doc['comparison_gamma']}")
    if "gammas" in summary_doc:
        lines.append("gammas:")
        lines.extend(f"  - {gamma}" for gamma in summary_doc["gammas"])
    Path(path).write_text("\n".join(lines) + "\n")


def write_metrics_summary_csv(path: str | Path, summary_doc: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for item in _summary_rows(summary_doc):
        aggregate = item["aggregate"]
        row = {
            "schema_version": SCHEMA_VERSION,
            "experiment_id": summary_doc.get("experiment_id", ""),
            "scenario_id": summary_doc.get("scenario_id", ""),
            "backend": summary_doc.get("backend", ""),
            "solver": summary_doc.get("solver", ""),
            "label": item["label"],
            "method": item["method"],
            "gamma": "" if item["gamma"] is None else item["gamma"],
            "runs": aggregate.get("runs", ""),
            "success_rate_mean": aggregate.get("success_rate", ""),
            "collision_rate_mean": aggregate.get("collision_rate", ""),
            "min_clearance_mean": aggregate.get("min_clearance_mean", ""),
            "min_obstacle_distance_mean": aggregate.get("min_obstacle_distance_mean", ""),
            "path_length_mean": aggregate.get("path_length_mean", ""),
            "completion_time_mean": aggregate.get("completion_time_mean", ""),
            "mean_solve_time_ms": aggregate.get("mean_solve_time_ms", ""),
            "p95_solve_time_ms": aggregate.get("p95_solve_time_ms", ""),
            "max_solve_time_ms": aggregate.get("max_solve_time_ms", ""),
            "solver_failure_rate_mean": aggregate.get("solver_failure_rate", ""),
            "solver_failures_mean": aggregate.get("solver_failures_mean", ""),
        }
        row.update(_ci_columns(aggregate))
        rows.append(json_ready(row))
    write_csv(path, rows)


def write_per_seed_metrics_csv(path: str | Path, summary_doc: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for item in _summary_rows(summary_doc):
        for run in item["runs"]:
            rows.append(
                json_ready(
                    {
                        "experiment": summary_doc.get("experiment_id", ""),
                        "scenario": run.get("scenario_id", summary_doc.get("scenario_id", "")),
                        "controller": _controller_name(run.get("method", item["method"])),
                        "backend": run.get("backend", summary_doc.get("backend", "")),
                        "seed": run.get("seed", ""),
                        "gamma": "" if run.get("gamma") is None else run.get("gamma", ""),
                        "success": run.get("success", ""),
                        "collision": run.get("collision", ""),
                        "min_clearance": run.get("min_clearance", ""),
                        "path_length": run.get("path_length", ""),
                        "completion_time": run.get("completion_time", ""),
                        "mean_solve_time": run.get("mean_solve_time_ms", ""),
                        "p95_solve_time": run.get("p95_solve_time_ms", ""),
                        "solver_failures": run.get("solver_failures", ""),
                    }
                )
            )
    write_csv(
        path,
        rows,
        fieldnames=[
            "experiment",
            "scenario",
            "controller",
            "backend",
            "seed",
            "gamma",
            "success",
            "collision",
            "min_clearance",
            "path_length",
            "completion_time",
            "mean_solve_time",
            "p95_solve_time",
            "solver_failures",
        ],
    )


def write_trajectory_files(path: str | Path, trace_rows: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[int, str, str], list[dict[str, Any]]] = defaultdict(list)
    gammas_by_method: dict[str, set[str]] = defaultdict(set)
    for row in trace_rows:
        seed = int(row["seed"])
        method = str(row["method"])
        gamma = str(row.get("gamma", ""))
        grouped[(seed, method, gamma)].append(row)
        gammas_by_method[method].add(gamma)

    for (seed, method, gamma), rows in grouped.items():
        label = method
        if gamma and len(gammas_by_method[method]) > 1:
            label = f"{method}_gamma_{gamma}"
        write_trace_csv(Path(path) / f"seed_{seed:03d}_{_slug(label)}.csv", rows)


def write_standard_figures(
    path: str | Path,
    scenario: Scenario,
    seed_zero_traces: dict[str, list[dict[str, Any]]],
    summary_doc: dict[str, Any],
) -> None:
    if seed_zero_traces:
        plot_trajectory(Path(path) / "seed_000_overlay.png", scenario, seed_zero_traces)
        plot_distance(Path(path) / "seed_000_clearance_curve.png", seed_zero_traces)
    grouped_clearance: dict[str, list[float]] = {}
    grouped_solve: dict[str, list[float]] = {}
    for item in _summary_rows(summary_doc):
        grouped_clearance[item["label"]] = [float(run["min_clearance"]) for run in item["runs"]]
        grouped_solve[item["label"]] = [float(run["mean_solve_time_ms"]) for run in item["runs"]]
    plot_metric_boxplot(Path(path) / "clearance_boxplot.png", grouped_clearance, "minimum clearance [m]", "Clearance by method")
    plot_metric_boxplot(Path(path) / "solve_time_boxplot.png", grouped_solve, "mean solve time [ms]", "Solve time by method")


def write_report(path: str | Path, summary_doc: dict[str, Any]) -> None:
    lines = [
        f"# {summary_doc.get('experiment_id', '')} Standard Artifact Report",
        "",
        f"- Schema: `{SCHEMA_VERSION}`",
        f"- Scenario: `{summary_doc.get('scenario_id', '')}`",
        f"- Backend: `{summary_doc.get('backend', '')}`",
        f"- Solver: `{summary_doc.get('solver', '')}`",
        "",
        "## Metrics Summary",
        "",
        "| Method | Runs | Success | Collision | Clearance | Solve time |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in _summary_rows(summary_doc):
        aggregate = item["aggregate"]
        lines.append(
            "| {label} | {runs} | {success:.3f} | {collision:.3f} | {clearance:.3f} | {solve:.3f} |".format(
                label=item["label"],
                runs=aggregate.get("runs", 0),
                success=float(aggregate.get("success_rate", 0.0)),
                collision=float(aggregate.get("collision_rate", 0.0)),
                clearance=float(aggregate.get("min_clearance_mean", 0.0)),
                solve=float(aggregate.get("mean_solve_time_ms", 0.0)),
            )
        )
    lines.extend(
        [
            "",
            "## Artifact Layout",
            "",
            "- `config.yaml`: machine-readable experiment configuration for later LaMPC/LLM blocks.",
            "- `metrics_summary.csv`: aggregate metrics with confidence interval columns.",
            "- `per_seed_metrics.csv`: one row per seed and method.",
            "- `trajectories/`: one trajectory CSV per seed and method.",
            "- `figures/`: representative overlay, clearance curve, and boxplots.",
            "- `logs/run.log`: run metadata and artifact counts.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n")


def write_run_log(path: str | Path, summary_doc: dict[str, Any], trace_rows: list[dict[str, Any]]) -> None:
    method_count = len(_summary_rows(summary_doc))
    seed_count = len({int(row["seed"]) for row in trace_rows})
    lines = [
        f"timestamp_utc={datetime.now(timezone.utc).isoformat()}",
        f"schema_version={SCHEMA_VERSION}",
        f"experiment_id={summary_doc.get('experiment_id', '')}",
        f"scenario_id={summary_doc.get('scenario_id', '')}",
        f"backend={summary_doc.get('backend', '')}",
        f"solver={summary_doc.get('solver', '')}",
        f"seeds={seed_count}",
        f"method_groups={method_count}",
        f"trace_rows={len(trace_rows)}",
    ]
    Path(path).write_text("\n".join(lines) + "\n")


def _summary_rows(summary_doc: dict[str, Any]) -> list[dict[str, Any]]:
    if "aggregate" in summary_doc:
        return [
            {
                "label": _label(summary_doc.get("method", ""), summary_doc.get("gamma")),
                "method": summary_doc.get("method", ""),
                "gamma": summary_doc.get("gamma"),
                "aggregate": summary_doc["aggregate"],
                "runs": summary_doc.get("runs", []),
            }
        ]

    rows: list[dict[str, Any]] = []
    for label, item in summary_doc.get("results", {}).items():
        method, gamma = _method_gamma_from_runs(item.get("runs", []), label)
        rows.append({"label": label, "method": method, "gamma": gamma, "aggregate": item["aggregate"], "runs": item["runs"]})
    for item in summary_doc.get("sweep", []):
        gamma = item["gamma"]
        rows.append(
            {
                "label": f"CBF gamma={gamma}",
                "method": "cbf",
                "gamma": gamma,
                "aggregate": item["aggregate"],
                "runs": item["runs"],
            }
        )
    return rows


def _ci_columns(aggregate: dict[str, Any]) -> dict[str, Any]:
    columns: dict[str, Any] = {}
    for key, stats in aggregate.get("ci", {}).items():
        columns[f"{key}_std"] = stats.get("std", "")
        columns[f"{key}_ci95"] = stats.get("ci95", "")
        columns[f"{key}_ci95_low"] = float(stats.get("mean", 0.0)) - float(stats.get("ci95", 0.0))
        columns[f"{key}_ci95_high"] = float(stats.get("mean", 0.0)) + float(stats.get("ci95", 0.0))
    return columns


def _seed_zero_traces(trace_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    gammas_by_method: dict[str, set[str]] = defaultdict(set)
    for row in trace_rows:
        if int(row["seed"]) != 0:
            continue
        gammas_by_method[str(row["method"])].add(str(row.get("gamma", "")))

    for row in trace_rows:
        if int(row["seed"]) != 0:
            continue
        method = str(row["method"])
        gamma = str(row.get("gamma", ""))
        label = method.upper() if method == "ed" else method
        if method == "cbf":
            label = "CBF" if len(gammas_by_method[method]) <= 1 else f"CBF gamma={gamma}"
        grouped[label].append(row)
    return dict(grouped)


def _method_gamma_from_runs(runs: list[dict[str, Any]], label: str) -> tuple[str, Any]:
    if runs:
        return str(runs[0].get("method", label)), runs[0].get("gamma")
    return label, ""


def _label(method: str, gamma: Any) -> str:
    if gamma is None or gamma == "":
        return method
    return f"{method} gamma={gamma}"


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_").lower()


def _controller_name(method: Any) -> str:
    value = str(method).lower()
    if value == "ed":
        return "ed"
    if value == "cbf":
        return "cbf"
    return value
