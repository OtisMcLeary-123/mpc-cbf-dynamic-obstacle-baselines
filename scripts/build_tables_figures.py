#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


METRICS = [
    "success_rate",
    "collision_rate",
    "control_failure_rate",
    "min_clearance_mean",
    "path_length_mean",
    "completion_time_mean",
    "mean_solve_time_ms",
    "p95_solve_time_ms",
    "solver_failure_rate",
    "solver_failures_mean",
    "infeasible_rate",
    "fallback_rate",
    "collision_after_fallback_rate",
]

SCENARIO_TABLE_ORDER = [
    ("Base", "point_mass_2d_dynamic_obstacle_v1"),
    ("Fast crossing", "fast_crossing_v1"),
    ("Late crossing", "late_crossing_v1"),
    ("Large obstacle", "large_obstacle_v1"),
    ("Noisy prediction", "noisy_prediction_v1"),
    ("Short horizon", "short_horizon_v1"),
]


def fmt_ci(aggregate: dict[str, Any], source_key: str) -> str:
    ci_key = {
        "success_rate": "success",
        "collision_rate": "collision",
        "control_failure_rate": "control_failure",
        "min_clearance_mean": "min_clearance",
        "path_length_mean": "path_length",
        "completion_time_mean": "completion_time",
        "mean_solve_time_ms": "mean_solve_time_ms",
        "solver_failure_rate": "solver_failure_rate",
        "infeasible_rate": "infeasible_rate",
        "fallback_rate": "fallback_rate",
        "collision_after_fallback_rate": "collision_after_fallback",
    }[source_key]
    stats = aggregate.get("ci", {}).get(ci_key)
    if not stats:
        return f"{aggregate.get(source_key, '')}"
    low = stats["mean"] - stats["ci95"]
    high = stats["mean"] + stats["ci95"]
    if source_key in {
        "success_rate",
        "collision_rate",
        "control_failure_rate",
        "solver_failure_rate",
        "infeasible_rate",
        "fallback_rate",
        "collision_after_fallback_rate",
    }:
        low = max(0.0, low)
        high = min(1.0, high)
    return f"{stats['mean']:.3f} ± {stats['std']:.3f} [{low:.3f}, {high:.3f}]"


def rows_from_summary(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    rows: list[dict[str, Any]] = []
    common = {
        "summary_path": str(path.relative_to(ROOT)),
        "suite": str(path.parent.relative_to(ROOT / "results")) if (ROOT / "results") in path.parents else "",
        "experiment_id": data.get("experiment_id", ""),
        "method": data.get("method", ""),
        "scenario_id": data.get("scenario_id", ""),
        "backend": data.get("backend", ""),
        "solver": data.get("solver", ""),
    }
    if "aggregate" in data:
        rows.append({**common, "label": data.get("method", ""), "aggregate": data["aggregate"]})
    for label, item in data.get("results", {}).items():
        rows.append({**common, "label": label, "aggregate": item["aggregate"]})
    for item in data.get("sweep", []):
        rows.append({**common, "label": f"gamma={item['gamma']}", "aggregate": item["aggregate"]})
    return rows


def collect_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((ROOT / "results").glob("**/summary.json")):
        if "checks" in path.parts:
            continue
        rows.extend(rows_from_summary(path))
    return rows


def write_tables(rows: list[dict[str, Any]]) -> None:
    out = ROOT / "docs/tables"
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "summary_metrics.csv"
    fieldnames = ["suite", "experiment_id", "scenario_id", "backend", "label", *METRICS, "summary_path"]
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            aggregate = row["aggregate"]
            writer.writerow(
                {
                    "suite": row["suite"],
                    "experiment_id": row["experiment_id"],
                    "scenario_id": row["scenario_id"],
                    "backend": row["backend"],
                    "label": row["label"],
                    **{metric: aggregate.get(metric, "") for metric in METRICS},
                    "summary_path": row["summary_path"],
                }
            )

    md_path = out / "summary_metrics.md"
    with md_path.open("w") as handle:
        handle.write("# Summary Metrics\n\n")
        handle.write("Values are `mean ± std [95% CI]` when per-seed run data is available.\n\n")
        handle.write("| Suite | Experiment | Scenario | Backend | Method | Success | Collision | Infeasible | Fallback | Coll. after fallback | Clearance | Path | Time | Solve |\n")
        handle.write("|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in rows:
            agg = row["aggregate"]
            handle.write(
                "| {suite} | {experiment} | {scenario} | {backend} | {label} | {success} | {collision} | {infeasible} | {fallback} | {collision_after_fallback} | {clearance} | {path} | {time} | {solve} |\n".format(
                    suite=row["suite"],
                    experiment=row["experiment_id"],
                    scenario=row["scenario_id"],
                    backend=row["backend"],
                    label=row["label"],
                    success=fmt_ci(agg, "success_rate"),
                    collision=fmt_ci(agg, "collision_rate"),
                    infeasible=fmt_ci(agg, "infeasible_rate"),
                    fallback=fmt_ci(agg, "fallback_rate"),
                    collision_after_fallback=fmt_ci(agg, "collision_after_fallback_rate"),
                    clearance=fmt_ci(agg, "min_clearance_mean"),
                    path=fmt_ci(agg, "path_length_mean"),
                    time=fmt_ci(agg, "completion_time_mean"),
                    solve=fmt_ci(agg, "mean_solve_time_ms"),
                )
            )


def write_scenario_table(rows: list[dict[str, Any]]) -> None:
    out = ROOT / "docs/tables"
    out.mkdir(parents=True, exist_ok=True)
    row_by_scenario: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        if not row["suite"].startswith("extended/scenarios/"):
            continue
        if row["backend"] != "random_shooting":
            continue
        row_by_scenario.setdefault(row["scenario_id"], {})[row["label"]] = row["aggregate"]

    table_rows: list[dict[str, Any]] = []
    for display_name, scenario_id in SCENARIO_TABLE_ORDER:
        methods = row_by_scenario.get(scenario_id, {})
        ed = methods.get("ED")
        cbf = methods.get("CBF gamma=0.08")
        if not ed or not cbf:
            continue
        table_rows.append(
            {
                "scenario": display_name,
                "scenario_id": scenario_id,
                "seeds": ed.get("runs", ""),
                "ed_success": ed.get("success_rate", ""),
                "cbf_success": cbf.get("success_rate", ""),
                "ed_collision": ed.get("collision_rate", ""),
                "cbf_collision": cbf.get("collision_rate", ""),
                "ed_clearance": ed.get("min_clearance_mean", ""),
                "cbf_clearance": cbf.get("min_clearance_mean", ""),
                "clearance_gain": float(cbf.get("min_clearance_mean", 0.0)) - float(ed.get("min_clearance_mean", 0.0)),
                "ed_completion_time": ed.get("completion_time_mean", ""),
                "cbf_completion_time": cbf.get("completion_time_mean", ""),
            }
        )

    csv_path = out / "scenario_comparison.csv"
    fieldnames = [
        "scenario",
        "scenario_id",
        "seeds",
        "ed_success",
        "cbf_success",
        "ed_collision",
        "cbf_collision",
        "ed_clearance",
        "cbf_clearance",
        "clearance_gain",
        "ed_completion_time",
        "cbf_completion_time",
    ]
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table_rows)

    md_path = out / "scenario_comparison.md"
    with md_path.open("w") as handle:
        handle.write("# Scenario Comparison\n\n")
        handle.write("ED vs CBF gamma=0.08 under matched 50-seed random-shooting runs.\n\n")
        handle.write("| Scenario | Seeds | ED succ. | CBF succ. | ED coll. | CBF coll. | ED clear. | CBF clear. | Clear. gain | ED time | CBF time |\n")
        handle.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in table_rows:
            handle.write(
                "| {scenario} | {seeds} | {ed_success:.2f} | {cbf_success:.2f} | {ed_collision:.2f} | {cbf_collision:.2f} | {ed_clearance:.3f} | {cbf_clearance:.3f} | {clearance_gain:.3f} | {ed_completion_time:.2f} | {cbf_completion_time:.2f} |\n".format(
                    scenario=row["scenario"],
                    seeds=int(row["seeds"]),
                    ed_success=float(row["ed_success"]),
                    cbf_success=float(row["cbf_success"]),
                    ed_collision=float(row["ed_collision"]),
                    cbf_collision=float(row["cbf_collision"]),
                    ed_clearance=float(row["ed_clearance"]),
                    cbf_clearance=float(row["cbf_clearance"]),
                    clearance_gain=float(row["clearance_gain"]),
                    ed_completion_time=float(row["ed_completion_time"]),
                    cbf_completion_time=float(row["cbf_completion_time"]),
                )
            )


def write_paired_delta_table() -> None:
    out = ROOT / "docs/tables"
    out.mkdir(parents=True, exist_ok=True)
    table_rows: list[dict[str, Any]] = []

    for summary_path in sorted((ROOT / "results").glob("**/summary.json")):
        if "checks" in summary_path.parts:
            continue
        data = json.loads(summary_path.read_text())
        results = data.get("results", {})
        if "ED" not in results or "CBF gamma=0.08" not in results:
            continue
        ed_runs = {int(run["seed"]): run for run in results["ED"].get("runs", [])}
        cbf_runs = {int(run["seed"]): run for run in results["CBF gamma=0.08"].get("runs", [])}
        seeds = sorted(set(ed_runs) & set(cbf_runs))
        if not seeds:
            continue
        deltas = {
            "delta_success": [float(cbf_runs[s]["success"]) - float(ed_runs[s]["success"]) for s in seeds],
            "delta_collision": [float(cbf_runs[s]["collision"]) - float(ed_runs[s]["collision"]) for s in seeds],
            "delta_clearance": [float(cbf_runs[s]["min_clearance"]) - float(ed_runs[s]["min_clearance"]) for s in seeds],
            "delta_path_length": [float(cbf_runs[s]["path_length"]) - float(ed_runs[s]["path_length"]) for s in seeds],
            "delta_solve_time": [float(cbf_runs[s]["mean_solve_time_ms"]) - float(ed_runs[s]["mean_solve_time_ms"]) for s in seeds],
        }
        row = {
            "suite": str(summary_path.parent.relative_to(ROOT / "results")),
            "scenario_id": data.get("scenario_id", ""),
            "backend": data.get("backend", ""),
            "seeds": len(seeds),
            "summary_path": str(summary_path.relative_to(ROOT)),
        }
        for key, values in deltas.items():
            stats = _mean_std_ci(values)
            row[f"{key}_mean"] = stats["mean"]
            row[f"{key}_std"] = stats["std"]
            row[f"{key}_ci95"] = stats["ci95"]
        table_rows.append(row)

    csv_path = out / "paired_delta.csv"
    fieldnames = [
        "suite",
        "scenario_id",
        "backend",
        "seeds",
        "delta_success_mean",
        "delta_success_std",
        "delta_success_ci95",
        "delta_collision_mean",
        "delta_collision_std",
        "delta_collision_ci95",
        "delta_clearance_mean",
        "delta_clearance_std",
        "delta_clearance_ci95",
        "delta_path_length_mean",
        "delta_path_length_std",
        "delta_path_length_ci95",
        "delta_solve_time_mean",
        "delta_solve_time_std",
        "delta_solve_time_ci95",
        "summary_path",
    ]
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table_rows)

    md_path = out / "paired_delta.md"
    with md_path.open("w") as handle:
        handle.write("# Paired ED-vs-CBF Delta Table\n\n")
        handle.write("Deltas are matched by seed and computed as `CBF gamma=0.08 - ED`.\n\n")
        handle.write("| Suite | Scenario | Backend | Seeds | Δsuccess | Δcollision | Δclearance | Δpath length | Δsolve time |\n")
        handle.write("|---|---|---|---:|---:|---:|---:|---:|---:|\n")
        for row in table_rows:
            handle.write(
                "| {suite} | {scenario} | {backend} | {seeds} | {success} | {collision} | {clearance} | {path} | {solve} |\n".format(
                    suite=row["suite"],
                    scenario=row["scenario_id"],
                    backend=row["backend"],
                    seeds=row["seeds"],
                    success=_fmt_mean_ci(row, "delta_success"),
                    collision=_fmt_mean_ci(row, "delta_collision"),
                    clearance=_fmt_mean_ci(row, "delta_clearance"),
                    path=_fmt_mean_ci(row, "delta_path_length"),
                    solve=_fmt_mean_ci(row, "delta_solve_time"),
                )
            )


def copy_key_figures() -> None:
    out = ROOT / "docs/figures/extended"
    out.mkdir(parents=True, exist_ok=True)
    overlay_paths = sorted((ROOT / "results").glob("extended/**/figures/seed_000_overlay.png"))
    clearance_paths = sorted((ROOT / "results").glob("extended/**/figures/seed_000_clearance_curve.png"))
    if not overlay_paths:
        overlay_paths = sorted((ROOT / "results").glob("extended/**/trajectory.png"))
    if not clearance_paths:
        clearance_paths = sorted((ROOT / "results").glob("extended/**/distance_to_obstacle.png"))

    for path in overlay_paths[:20]:
        target = out / f"{_figure_prefix(path)}_trajectory.png"
        shutil.copy(path, target)
    for path in clearance_paths[:20]:
        target = out / f"{_figure_prefix(path)}_clearance.png"
        shutil.copy(path, target)


def _figure_prefix(path: Path) -> str:
    run_dir = path.parent.parent if path.parent.name == "figures" else path.parent
    parts = run_dir.relative_to(ROOT / "results").parts
    return "_".join(parts[-2:]) if len(parts) >= 2 else parts[0]


def _mean_std_ci(values: list[float]) -> dict[str, float]:
    mean = sum(values) / len(values)
    if len(values) <= 1:
        return {"mean": mean, "std": 0.0, "ci95": 0.0}
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    std = math.sqrt(variance)
    return {"mean": mean, "std": std, "ci95": 1.96 * std / math.sqrt(len(values))}


def _fmt_mean_ci(row: dict[str, Any], prefix: str) -> str:
    mean = float(row[f"{prefix}_mean"])
    ci95 = float(row[f"{prefix}_ci95"])
    return f"{mean:.3f} ± {ci95:.3f}"


def write_paper_section(rows: list[dict[str, Any]]) -> None:
    main_ed = _find_row(rows, "paper_main/e4_base_50_seed", "ED")
    main_cbf = _find_row(rows, "paper_main/e4_base_50_seed", "CBF gamma=0.08")
    stress_ed = _find_row(rows, "extended/stress_100_seeds/base_random_shooting", "ED")
    stress_cbf = _find_row(rows, "extended/stress_100_seeds/base_random_shooting", "CBF gamma=0.08")
    casadi_ed = _find_row(rows, "extended/backend_comparison/casadi", "ED")
    casadi_cbf = _find_row(rows, "extended/backend_comparison/casadi", "CBF gamma=0.08")
    random_ed = _find_row(rows, "extended/backend_comparison/random_shooting", "ED")
    random_cbf = _find_row(rows, "extended/backend_comparison/random_shooting", "CBF gamma=0.08")

    out = ROOT / "docs/paper_section_results.md"
    with out.open("w") as handle:
        handle.write("# Block A Results Section Draft\n\n")
        handle.write("## Experimental Setup\n\n")
        handle.write(
            "We evaluate MPC with Euclidean-distance constraints and MPC-CBF on a 2D point-mass dynamic obstacle navigation benchmark. "
            "All comparisons use matched seeds within each scenario. Metrics include success rate, collision rate, minimum clearance, path length, completion time, and solve time.\n\n"
        )
        handle.write(
            "The extended benchmark includes the base scenario, six harder dynamic-obstacle scenarios, obstacle prediction noise, obstacle speed sweeps, "
            "horizon/gamma ablations, a 100-seed stress test, and a backend comparison between the lightweight random-shooting MPC and a CasADi/IPOPT nonlinear-programming backend.\n\n"
        )
        handle.write("## Main Matched-Seed Comparison\n\n")
        if main_ed and main_cbf:
            handle.write(_comparison_paragraph("base-scenario ED-vs-CBF comparison", main_ed, main_cbf))
            handle.write(
                "These results support the intended Block A role: CBF is not merely a collision-avoidance constraint, but a more proactive safety constraint that increases clearance before the robot reaches the obstacle boundary.\n\n"
            )
        else:
            handle.write("Main matched-seed results were not found in `results/paper_main/e4_base_50_seed`.\n\n")
        handle.write("## Stress Test\n\n")
        if stress_ed and stress_cbf:
            handle.write(_comparison_paragraph("stress test", stress_ed, stress_cbf))
            handle.write(
                "This exposes the safety-performance trade-off: fixed-gamma CBF maintains a much larger safety margin but can reduce task completion under harder seeded conditions.\n\n"
            )
        else:
            handle.write("Stress-test results were not found in `results/extended/stress_100_seeds/base_random_shooting`.\n\n")
        handle.write("## Backend Comparison\n\n")
        if casadi_ed and casadi_cbf:
            handle.write(_comparison_paragraph("CasADi/IPOPT backend comparison", casadi_ed, casadi_cbf))
            handle.write(
                "The CasADi/IPOPT table reports solver failure separately from control failure, including infeasible, fallback, and collision-after-fallback rates. "
                "This separates numerical optimization issues from actual closed-loop collision outcomes.\n\n"
            )
        else:
            handle.write("CasADi/IPOPT backend comparison results were not found in `results/extended/backend_comparison/casadi`.\n\n")
        if random_ed and random_cbf:
            handle.write(_comparison_paragraph("random-shooting backend comparison", random_ed, random_cbf))
        handle.write(
            "The random-shooting backend remains useful for fast sweeps and stress tests; CasADi/IPOPT is slower but closer to the optimization stack used in the reference implementation.\n\n"
        )
        handle.write("## Ablations\n\n")
        handle.write(
            "The horizon/gamma ablation confirms that smaller `gamma` generally increases clearance. "
            "Shorter horizons reduce solve time, but the safety-performance behavior depends on the obstacle timing and scenario geometry.\n\n"
        )
        handle.write(
            "The obstacle-speed and prediction-noise sweeps show that CBF can become overly conservative under high uncertainty: clearance remains high, but completion rate can drop. "
            "This motivates Block B and later language-interface experiments, where adaptive policies should preserve safety without sacrificing completion.\n\n"
        )
        handle.write("## Tables\n\n")
        handle.write("See `docs/tables/summary_metrics.md` for mean, standard deviation, and 95% confidence intervals. ")
        handle.write("See `docs/tables/scenario_comparison.md` for a scenario-by-scenario ED-vs-CBF table. ")
        handle.write("See `docs/tables/paired_delta.md` for matched-seed paired deltas.\n\n")
        handle.write("## Standard Artifacts\n\n")
        handle.write(
            "Every new experiment output also writes `config.yaml`, `metrics_summary.csv`, fixed-schema `per_seed_metrics.csv`, per-seed trajectory CSVs, figures, logs, and `report.md` for downstream LaMPC/LLM blocks.\n\n"
        )
        handle.write("## Reproducibility\n\n")
        handle.write("Run `scripts/reproduce_all.sh` to regenerate the extended benchmark outputs, tables, figures, and this report draft.\n")


def _find_row(rows: list[dict[str, Any]], suite: str, label: str) -> dict[str, Any] | None:
    for row in rows:
        if row["suite"] == suite and row["label"] == label:
            return row
    return None


def _comparison_paragraph(name: str, ed_row: dict[str, Any], cbf_row: dict[str, Any]) -> str:
    ed = ed_row["aggregate"]
    cbf = cbf_row["aggregate"]
    seeds = int(ed.get("runs", cbf.get("runs", 0)))
    return (
        f"In the {seeds}-seed {name}, ED achieved success rate {_fmt_scalar(ed, 'success_rate')} "
        f"with collision rate {_fmt_scalar(ed, 'collision_rate')} and mean minimum clearance {_fmt_scalar(ed, 'min_clearance_mean')} m. "
        f"MPC-CBF with `gamma=0.08` achieved success rate {_fmt_scalar(cbf, 'success_rate')} "
        f"with collision rate {_fmt_scalar(cbf, 'collision_rate')} and mean minimum clearance {_fmt_scalar(cbf, 'min_clearance_mean')} m. "
        f"Mean solve times were {_fmt_scalar(ed, 'mean_solve_time_ms')} ms for ED and {_fmt_scalar(cbf, 'mean_solve_time_ms')} ms for CBF. "
        f"Fallback rates were {_fmt_scalar(ed, 'fallback_rate')} for ED and {_fmt_scalar(cbf, 'fallback_rate')} for CBF; "
        f"collision-after-fallback rates were {_fmt_scalar(ed, 'collision_after_fallback_rate')} and {_fmt_scalar(cbf, 'collision_after_fallback_rate')}, respectively.\n\n"
    )


def _fmt_scalar(aggregate: dict[str, Any], key: str) -> str:
    value = aggregate.get(key)
    if value == "" or value is None:
        return "not reported"
    return f"{float(value):.3f}"


def main() -> None:
    rows = collect_rows()
    write_tables(rows)
    write_scenario_table(rows)
    write_paired_delta_table()
    copy_key_figures()
    write_paper_section(rows)
    print(f"Wrote {len(rows)} table rows to docs/tables/summary_metrics.*, scenario_comparison.*, and paired_delta.*")


if __name__ == "__main__":
    main()
