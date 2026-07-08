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
    "solver_failure_rate",
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
    for path in sorted((ROOT / "results").glob("extended/**/trajectory.png"))[:20]:
        target = out / f"{'_'.join(path.parts[-3:-1])}_trajectory.png"
        shutil.copy(path, target)
    for path in sorted((ROOT / "results").glob("extended/**/distance_to_obstacle.png"))[:20]:
        target = out / f"{'_'.join(path.parts[-3:-1])}_clearance.png"
        shutil.copy(path, target)


def write_paper_section(rows: list[dict[str, Any]]) -> None:
    out = ROOT / "docs/paper_section_results.md"
    with out.open("w") as handle:
        handle.write("# Block A Results Section Draft\n\n")
        handle.write("## Experimental Setup\n\n")
        handle.write(
            "We evaluate MPC with Euclidean-distance constraints and MPC-CBF on a 2D point-mass dynamic obstacle navigation benchmark. "
            "All comparisons use matched seeds within each scenario. Metrics include success rate, collision rate, minimum clearance, path length, completion time, and solve time.\n\n"
        )
        handle.write("## Main Finding\n\n")
        handle.write(
            "Across the generated summaries, CBF variants primarily improve proactive clearance relative to ED. "
            "Collision-rate separation depends on scenario difficulty; therefore, harder crossing scenarios and stress tests are included for paper-level evaluation.\n\n"
        )
        handle.write("## Tables\n\n")
        handle.write("See `docs/tables/summary_metrics.md` for mean, standard deviation, and 95% confidence intervals.\n\n")
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
