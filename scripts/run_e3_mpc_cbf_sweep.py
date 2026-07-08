#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from block_a.runner import run_e3_sweep


def main() -> None:
    parser = argparse.ArgumentParser(description="Run E3 MPC-CBF gamma sweep.")
    parser.add_argument("--scenario", default=ROOT / "configs/scenario_point_mass_2d.json")
    parser.add_argument("--output", default=ROOT / "results/exp_e3")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--gammas", type=float, nargs="+", default=[1.0, 0.15, 0.08, 0.04, 0.02])
    parser.add_argument("--backend", choices=["random_shooting", "casadi"], default="random_shooting")
    parser.add_argument("--casadi-horizon", type=int, default=8)
    args = parser.parse_args()
    run_e3_sweep(
        args.scenario,
        args.output,
        seeds=args.seeds,
        gammas=args.gammas,
        backend=args.backend,
        casadi_horizon=args.casadi_horizon,
    )
    print(f"Wrote E3 results to {args.output}")


if __name__ == "__main__":
    main()
