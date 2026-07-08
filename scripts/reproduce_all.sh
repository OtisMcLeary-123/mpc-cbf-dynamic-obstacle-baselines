#!/usr/bin/env bash
set -euo pipefail

# Main 50-seed matched ED vs CBF comparison on the base scenario.
python3 scripts/run_e4_compare_ed_cbf.py --seeds 50 --gamma 0.08 --output results/paper_main/e4_base_50_seed

# Four to six harder scenarios, matched seeds.
python3 scripts/run_extended_suite.py --suite scenarios --seeds 50 --gamma 0.08

# Obstacle prediction noise, obstacle speed, horizon/gamma ablations.
python3 scripts/run_extended_suite.py --suite prediction-noise --seeds 20 --gamma 0.08
python3 scripts/run_extended_suite.py --suite speed-sweep --seeds 20 --gamma 0.08
python3 scripts/run_extended_suite.py --suite horizon-gamma --seeds 20

# Stress test with 100 seeds.
python3 scripts/run_extended_suite.py --suite stress --stress-seeds 100 --gamma 0.08

# CasADi/IPOPT backend comparison. Kept small by default because IPOPT is much slower.
python3 scripts/run_extended_suite.py --suite backend --seeds 5 --gamma 0.08 --casadi-horizon 8

# Tables, selected figures, and paper-style section.
python3 scripts/build_tables_figures.py
