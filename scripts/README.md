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
experiment,scenario,controller,backend,seed,gamma,success,collision,min_clearance,path_length,completion_time,mean_solve_time,p95_solve_time,solver_failures
```
