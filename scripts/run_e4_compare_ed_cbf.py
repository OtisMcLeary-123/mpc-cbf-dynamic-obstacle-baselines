#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from block_a.runner import run_e4_comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Run E4 ED vs CBF matched-seed comparison.")
    parser.add_argument("--scenario", default=ROOT / "configs/scenario_point_mass_2d.json")
    parser.add_argument("--output", default=ROOT / "results/exp_e4")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--gamma", type=float, default=0.08)
    parser.add_argument("--backend", choices=["random_shooting", "casadi"], default="random_shooting")
    parser.add_argument("--casadi-horizon", type=int, default=8)
    args = parser.parse_args()
    run_e4_comparison(
        args.scenario,
        args.output,
        seeds=args.seeds,
        gamma=args.gamma,
        backend=args.backend,
        casadi_horizon=args.casadi_horizon,
    )
    print(f"Wrote E4 results to {args.output}")


if __name__ == "__main__":
    main()
