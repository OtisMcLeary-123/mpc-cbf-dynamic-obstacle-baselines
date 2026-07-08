#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from block_a.runner import run_e3_sweep, run_e4_comparison


BASE_SCENARIO = ROOT / "configs/scenario_point_mass_2d.json"
SCENARIO_DIR = ROOT / "configs/scenarios"


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_").lower()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def scenario_paths() -> list[Path]:
    return [BASE_SCENARIO] + sorted(SCENARIO_DIR.glob("*.json"))


def run_scenarios(seeds: int, gamma: float, backend: str, casadi_horizon: int) -> None:
    for scenario in scenario_paths():
        scenario_id = load_json(scenario)["scenario_id"]
        out = ROOT / "results/extended/scenarios" / slug(f"{scenario_id}_{backend}")
        run_e4_comparison(
            scenario,
            out,
            seeds=seeds,
            gamma=gamma,
            backend=backend,
            casadi_horizon=casadi_horizon,
        )


def run_backend_comparison(seeds: int, gamma: float, casadi_horizon: int) -> None:
    for backend in ["random_shooting", "casadi"]:
        out = ROOT / "results/extended/backend_comparison" / backend
        run_e4_comparison(BASE_SCENARIO, out, seeds=seeds, gamma=gamma, backend=backend, casadi_horizon=casadi_horizon)


def run_prediction_noise(seeds: int, gamma: float) -> None:
    base = load_json(BASE_SCENARIO)
    for noise in [0.0, 0.03, 0.06, 0.10]:
        data = json.loads(json.dumps(base))
        data["scenario_id"] = f"prediction_noise_{noise:.2f}"
        data["simulation"]["obstacle_prediction_noise_std"] = [noise, noise]
        config = write_json(ROOT / "results/generated_configs" / f"prediction_noise_{noise:.2f}.json", data)
        out = ROOT / "results/extended/prediction_noise" / slug(data["scenario_id"])
        run_e4_comparison(config, out, seeds=seeds, gamma=gamma)


def run_speed_sweep(seeds: int, gamma: float) -> None:
    base = load_json(BASE_SCENARIO)
    for speed in [0.20, 0.35, 0.50, 0.65]:
        data = json.loads(json.dumps(base))
        data["scenario_id"] = f"obstacle_speed_{speed:.2f}"
        data["obstacle"]["velocity"] = [0.0, speed]
        config = write_json(ROOT / "results/generated_configs" / f"obstacle_speed_{speed:.2f}.json", data)
        out = ROOT / "results/extended/speed_sweep" / slug(data["scenario_id"])
        run_e4_comparison(config, out, seeds=seeds, gamma=gamma)


def run_horizon_gamma(seeds: int) -> None:
    base = load_json(BASE_SCENARIO)
    gammas = [0.15, 0.08, 0.04]
    for horizon in [8, 12, 20]:
        data = json.loads(json.dumps(base))
        data["scenario_id"] = f"horizon_{horizon}"
        data["simulation"]["horizon_steps"] = horizon
        config = write_json(ROOT / "results/generated_configs" / f"horizon_{horizon}.json", data)
        out = ROOT / "results/extended/horizon_gamma" / f"horizon_{horizon}"
        run_e3_sweep(config, out, seeds=seeds, gammas=gammas)


def run_stress(seeds: int, gamma: float) -> None:
    out = ROOT / "results/extended/stress_100_seeds/base_random_shooting"
    run_e4_comparison(BASE_SCENARIO, out, seeds=seeds, gamma=gamma)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run extended Block A experiment suites.")
    parser.add_argument(
        "--suite",
        choices=["scenarios", "backend", "prediction-noise", "speed-sweep", "horizon-gamma", "stress", "all"],
        default="all",
    )
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--stress-seeds", type=int, default=100)
    parser.add_argument("--gamma", type=float, default=0.08)
    parser.add_argument("--backend", choices=["random_shooting", "casadi"], default="random_shooting")
    parser.add_argument("--casadi-horizon", type=int, default=8)
    args = parser.parse_args()

    if args.suite in {"scenarios", "all"}:
        run_scenarios(args.seeds, args.gamma, args.backend, args.casadi_horizon)
    if args.suite in {"backend", "all"}:
        run_backend_comparison(max(2, args.seeds), args.gamma, args.casadi_horizon)
    if args.suite in {"prediction-noise", "all"}:
        run_prediction_noise(args.seeds, args.gamma)
    if args.suite in {"speed-sweep", "all"}:
        run_speed_sweep(args.seeds, args.gamma)
    if args.suite in {"horizon-gamma", "all"}:
        run_horizon_gamma(args.seeds)
    if args.suite in {"stress", "all"}:
        run_stress(args.stress_seeds, args.gamma)


if __name__ == "__main__":
    main()
