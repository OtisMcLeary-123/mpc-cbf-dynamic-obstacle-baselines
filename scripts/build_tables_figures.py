#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


METRICS = [
    "success_rate",
    "collision_rate",
    "min_clearance_mean",
    "path_length_mean",
    "completion_time_mean",
    "mean_solve_time_ms",
    "p95_solve_time_ms",
    "solver_failure_rate",
    "solver_failures_mean",
]


def fmt_ci(aggregate: dict[str, Any], source_key: str) -> str:
    ci_key = {
        "success_rate": "success",
        "collision_rate": "collision",
        "min_clearance_mean": "min_clearance",
        "path_length_mean": "path_length",
        "completion_time_mean": "completion_time",
        "mean_solve_time_ms": "mean_solve_time_ms",
        "solver_failure_rate": "solver_failure_rate",
    }[source_key]
    stats = aggregate.get("ci", {}).get(ci_key)
    if not stats:
        return f"{aggregate.get(source_key, '')}"
    low = stats["mean"] - stats["ci95"]
    high = stats["mean"] + stats["ci95"]
    if source_key in {"success_rate", "collision_rate", "solver_failure_rate"}:
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
        handle.write("| Suite | Experiment | Scenario | Backend | Method | Success | Collision | Clearance | Path | Time | Solve |\n")
        handle.write("|---|---|---|---|---|---:|---:|---:|---:|---:|---:|\n")
        for row in rows:
            agg = row["aggregate"]
            handle.write(
                "| {suite} | {experiment} | {scenario} | {backend} | {label} | {success} | {collision} | {clearance} | {path} | {time} | {solve} |\n".format(
                    suite=row["suite"],
                    experiment=row["experiment_id"],
                    scenario=row["scenario_id"],
                    backend=row["backend"],
                    label=row["label"],
                    success=fmt_ci(agg, "success_rate"),
                    collision=fmt_ci(agg, "collision_rate"),
                    clearance=fmt_ci(agg, "min_clearance_mean"),
                    path=fmt_ci(agg, "path_length_mean"),
                    time=fmt_ci(agg, "completion_time_mean"),
                    solve=fmt_ci(agg, "mean_solve_time_ms"),
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


def write_paper_section(rows: list[dict[str, Any]]) -> None:
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
        handle.write(
            "In the 50-seed base-scenario ED-vs-CBF comparison, ED achieved a success rate of 0.84 with zero collisions and a mean minimum clearance of 0.058 m. "
            "MPC-CBF with `gamma=0.08` achieved a success rate of 0.86 with zero collisions and a substantially larger mean minimum clearance of 0.823 m. "
            "Mean solve times were similar: 1.825 ms for ED and 1.851 ms for CBF under the random-shooting backend.\n\n"
        )
        handle.write(
            "These results support the intended Block A role: CBF is not merely a collision-avoidance constraint, but a more proactive safety constraint that increases clearance before the robot reaches the obstacle boundary.\n\n"
        )
        handle.write("## Stress Test\n\n")
        handle.write(
            "In the 100-seed stress test, ED achieved a success rate of 0.89 with mean clearance 0.054 m, while CBF achieved success rate 0.81 with mean clearance 0.824 m. "
            "This exposes the safety-performance trade-off: fixed-gamma CBF maintains a much larger safety margin but can reduce task completion under harder seeded conditions.\n\n"
        )
        handle.write("## Backend Comparison\n\n")
        handle.write(
            "The CasADi/IPOPT backend was implemented for both MPC-ED and MPC-CBF. "
            "In the small matched-seed backend comparison, CasADi/IPOPT ED achieved success rate 0.20 and collision rate 0.80, while CasADi/IPOPT CBF achieved success rate 1.00 and collision rate 0.00. "
            "This mirrors the qualitative claim from the reference paper: distance constraints can ride the obstacle boundary, while CBF constraints enforce more proactive avoidance.\n\n"
        )
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
        handle.write("See `docs/tables/summary_metrics.md` for mean, standard deviation, and 95% confidence intervals.\n\n")
        handle.write("## Standard Artifacts\n\n")
        handle.write(
            "Every new experiment output also writes `config.yaml`, `metrics_summary.csv`, fixed-schema `per_seed_metrics.csv`, per-seed trajectory CSVs, figures, logs, and `report.md` for downstream LaMPC/LLM blocks.\n\n"
        )
        handle.write("## Reproducibility\n\n")
        handle.write("Run `scripts/reproduce_all.sh` to regenerate the extended benchmark outputs, tables, figures, and this report draft.\n")


def main() -> None:
    rows = collect_rows()
    write_tables(rows)
    copy_key_figures()
    write_paper_section(rows)
    print(f"Wrote {len(rows)} table rows to docs/tables/summary_metrics.*")


if __name__ == "__main__":
    main()
