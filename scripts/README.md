# Scripts

This directory will contain experiment runners and plotting commands for Block A.

Entrypoints:

```text
run_e0_smoke.py
run_e2_mpc_ed.py
run_e3_mpc_cbf_sweep.py
run_e4_compare_ed_cbf.py
run_block_a_smoke.sh
run_extended_suite.py
build_tables_figures.py
reproduce_all.sh
```

Example:

```bash
bash scripts/run_block_a_smoke.sh
```

Paper-level reproduction:

```bash
bash scripts/reproduce_all.sh
```

The paper-level script runs CasADi/IPOPT backend comparison with 20 matched seeds by default. For a larger backend-only run:

```bash
python3 scripts/run_extended_suite.py --suite backend --seeds 50 --gamma 0.08 --casadi-horizon 8
python3 scripts/build_tables_figures.py
```

Each runner writes the standard artifact contract under its output directory:

```text
config.yaml
metrics_summary.csv
per_seed_metrics.csv
trajectories/
figures/
logs/run.log
report.md
```

The fixed `per_seed_metrics.csv` header is:

```text
experiment,scenario,controller,backend,seed,gamma,success,collision,min_clearance,path_length,completion_time,mean_solve_time,p95_solve_time,solver_failures,infeasible_rate,fallback_rate,collision_after_fallback,control_failure
```

Generated paper tables include:

```text
docs/tables/summary_metrics.md
docs/tables/scenario_comparison.md
docs/tables/paired_delta.md
```
