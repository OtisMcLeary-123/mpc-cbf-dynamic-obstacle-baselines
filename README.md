# MPC-CBF Dynamic Obstacle Baselines

## Goal

This repository contains reproducible Model Predictive Control (MPC) and Control Barrier Function (CBF) baselines for dynamic obstacle avoidance.

It is Block A of the larger LaMPC-CBF reference micro-experiment workspace.

Block A focuses on control baselines before any language/LLM interface is added:

```text
E0 -> E2 -> E3 -> E4
```

The goal is to establish a reliable, measurable MPC-CBF baseline for a small dynamic-obstacle navigation scenario.

## Research Role

Block A answers the control foundation question:

```text
Does MPC-CBF provide safer and more proactive obstacle avoidance than
Euclidean-distance constrained MPC under the same scenario, seeds, and metrics?
```

This block is required before testing language interfaces in later repos:

- Block B: strong non-LLM adaptive safety baselines
- Block C: language interface comparison
- Block D: closest paper baselines
- Block E: evaluation and paper figures

## Experiments

| ID | Method | Purpose | Expected output |
|---|---|---|---|
| E0 | MPC smoke test | Verify solver stability without obstacles | Tracking error and solve-time report |
| E2 | MPC-ED | Euclidean distance constrained MPC baseline | Collision/min-distance baseline |
| E3 | MPC-CBF | Discrete-time CBF gamma sweep | Safety-performance gamma curve |
| E4 | ED vs CBF | Direct comparison under identical scenario | Evidence that CBF is more proactive than ED |

## References Needed For This Block

These references come from:

```text
/home/otismcleary/Documents/paper/Safety-Aware_Optimal_Control_With_Language-Guided_Online_Parameter_Adjustment_via_Large_Language_Models.pdf
```

Local reading corpus:

```text
papers/manifest.md
```

PDF files in `papers/` are stored locally for reading and ignored by Git. The manifest records source URLs, local filenames, and checksum values.

Required references:

| Ref | Paper | Used by | Why needed |
|---|---|---|---|
| [2] | Garcia, Prett, and Morari, "Model predictive control: Theory and practice - A survey," 1989 | E0, E2, E3, E4 | General model predictive control foundation. |
| [3] | Zeng, Zhang, and Sreenath, "Safety-critical model predictive control with discrete-time control barrier function," 2021 | E3, E4 | Safety-critical MPC with discrete-time CBF. |
| [4] | Ames et al., "Control barrier functions: Theory and applications," 2019 | E3 | Core control barrier function theory. |
| [47] | Agrawal and Sreenath, "Discrete control barrier functions for safety-critical control of discrete systems with application to bipedal robot navigation," 2017 | E3 | Discrete control barrier functions. |
| [48] | Andersson et al., "CasADi: A software framework for nonlinear optimization and optimal control," 2019 | E0, E2, E3, E4 | CasADi nonlinear optimization framework. |
| [51] | Fiedler et al., "Do-mpc: Towards FAIR nonlinear and robust model predictive control," 2023 | E0, E2, E3, E4 | do-mpc implementation reference, if do-mpc is used. |
| [52] | Wachter and Biegler, "On the implementation of an interior-point filter line-search algorithm for large-scale nonlinear programming," 2006 | E0, E2, E3, E4 | IPOPT solver reference. |

Optional references for stronger related work:

| Ref | Paper | Used by | Why useful |
|---|---|---|---|
| [5] | Jian et al., "Dynamic control barrier function-based model predictive control to safety-critical obstacle-avoidance of mobile robot," 2023 | Background | Dynamic CBF-MPC obstacle avoidance for mobile robots. |
| [7] | Vulcano et al., "Safe robot navigation in a crowd combining NMPC and control barrier functions," 2022 | Background | Safe navigation with NMPC and CBF. |
| [10] | Zhang et al., "Online efficient safety-critical control for mobile robots in unknown dynamic multi-obstacle environments," 2024 | Background | Safety-critical control in unknown dynamic multi-obstacle environments. |

References deferred to other blocks:

| Ref | Block | Reason |
|---|---|---|
| [1], [33]-[35] | Optional E1/APF baseline | Only needed if artificial potential field is added back. |
| [9], [11] | Block B | Adaptive/rate-tunable CBF, not fixed CBF baseline. |
| [31], [32], [38] | Block C/D | Language-to-MPC and language-guided MPC baselines. |
| [39]-[44] | Block C | Language trajectory correction/editing. |
| [55], [56] | Block E | Language-behavior alignment metrics. |

## Shared Scenario

```text
Robot: point-mass 2D
Task: move from start to target
Obstacle: dynamic circle crossing the direct path
Seeds: 10 for smoke/dev runs, 50 for paper-level results
```

Default metrics:

```text
success_rate
collision_rate
min_obstacle_distance_mean
min_obstacle_distance_std
path_length
completion_time
mean_solve_time_ms
p95_solve_time_ms
solver_failure_rate
solver_failures
control_failure_rate
infeasible_rate
fallback_rate
collision_after_fallback_rate
```

## Repository Structure

```text
configs/   scenario and experiment configs
docs/      experiment protocol, reports, and log
results/   generated summaries, traces, and plots
scripts/   runner and plotting entrypoints
src/       shared implementation
```

## Quickstart

Install minimal dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the smoke/dev benchmark:

```bash
bash scripts/run_block_a_smoke.sh
```

Run the 10-seed dev benchmark:

```bash
python3 scripts/run_e0_smoke.py --seeds 10
python3 scripts/run_e2_mpc_ed.py --seeds 10
python3 scripts/run_e3_mpc_cbf_sweep.py --seeds 10
python3 scripts/run_e4_compare_ed_cbf.py --seeds 10 --gamma 0.08
```

Generated outputs are written under `results/exp_e*/` and are ignored by Git.

## Standard Result Schema

Each experiment writes the following machine-readable artifact layout for later LaMPC/LLM blocks:

```text
results/
  experiment_name/
    config.yaml
    metrics_summary.csv
    per_seed_metrics.csv
    trajectories/
      seed_000_ed.csv
      seed_000_cbf.csv
    figures/
      seed_000_overlay.png
      seed_000_clearance_curve.png
      clearance_boxplot.png
      solve_time_boxplot.png
    logs/
      run.log
    report.md
```

`per_seed_metrics.csv` has a fixed header:

```text
experiment,scenario,controller,backend,seed,gamma,success,collision,min_clearance,path_length,completion_time,mean_solve_time,p95_solve_time,solver_failures,infeasible_rate,fallback_rate,collision_after_fallback,control_failure
```

Legacy files (`summary.json`, `trace.csv`, `trajectory.png`, and `distance_to_obstacle.png`) are still written for backward compatibility with earlier Block A scripts and docs.

## Latest Dev Results

Last local run: 2026-07-08, 10 seeds.

Solver implementation:

```text
numpy_random_shooting_mpc
```

Full report:

```text
docs/exp_e0_e4_smoke_report.md
```

Summary:

| Experiment | Method | Seeds | Success rate | Collision rate | Mean min clearance | Mean path length | Mean completion time | Mean solve time |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| E0 | Smoke tracking, no obstacle constraint | 10 | 1.00 | 0.00 | not used | 4.813 m | 4.30 s | 0.008 ms |
| E2 | MPC-ED | 10 | 0.90 | 0.00 | 0.049 m | 5.142 m | 5.00 s | 1.772 ms |
| E3 | MPC-CBF, gamma=1.0 | 10 | 0.90 | 0.00 | 0.051 m | 5.149 m | 4.97 s | 1.819 ms |
| E3 | MPC-CBF, gamma=0.15 | 10 | 0.90 | 0.00 | 0.485 m | 5.374 m | 4.85 s | 1.818 ms |
| E3 | MPC-CBF, gamma=0.08 | 10 | 0.90 | 0.00 | 0.812 m | 5.779 m | 5.26 s | 1.813 ms |
| E3 | MPC-CBF, gamma=0.04 | 10 | 0.90 | 0.00 | 1.045 m | 6.475 m | 6.83 s | 1.821 ms |
| E3 | MPC-CBF, gamma=0.02 | 10 | 0.90 | 0.00 | 1.139 m | 6.747 m | 7.41 s | 1.819 ms |
| E4 | ED matched-seed comparison | 10 | 0.90 | 0.00 | 0.049 m | 5.142 m | 5.00 s | 1.779 ms |
| E4 | CBF gamma=0.08 matched-seed comparison | 10 | 0.90 | 0.00 | 0.812 m | 5.779 m | 5.26 s | 1.826 ms |

Current interpretation:

- E0 confirms the no-obstacle tracking loop runs successfully.
- E3 shows the expected gamma trend: smaller `gamma` produces larger obstacle clearance.
- E4 shows CBF is more proactive than ED in this scenario: `gamma=0.08` increases mean clearance from `0.049 m` to `0.812 m` with similar solve time.
- ED already has zero collision in this 10-seed dev scenario, so this scenario currently separates methods mainly by clearance, not collision rate.

## Result Figures

These figures are copied from the latest local `results/exp_e*/` run into `docs/figures/` so they render on GitHub.

### E0: Smoke Tracking

Trajectory:

![E0 trajectory](docs/figures/e0_trajectory.png)

Distance to obstacle:

![E0 distance to obstacle](docs/figures/e0_distance_to_obstacle.png)

### E2: MPC-ED

Trajectory:

![E2 trajectory](docs/figures/e2_trajectory.png)

Distance to obstacle:

![E2 distance to obstacle](docs/figures/e2_distance_to_obstacle.png)

### E3: MPC-CBF Gamma Sweep

Trajectory:

![E3 trajectory](docs/figures/e3_trajectory.png)

Distance to obstacle:

![E3 distance to obstacle](docs/figures/e3_distance_to_obstacle.png)

### E4: ED vs CBF

Trajectory:

![E4 trajectory](docs/figures/e4_trajectory.png)

Distance to obstacle:

![E4 distance to obstacle](docs/figures/e4_distance_to_obstacle.png)

## Extended Paper-Level Benchmark

The extended suite is generated by:

```bash
bash scripts/reproduce_all.sh
```

It covers:

- 6 harder scenarios plus the base scenario.
- ED vs CBF matched seeds with 50 seeds.
- Mean, standard deviation, and 95% confidence interval tables.
- Trajectory overlays and clearance curves.
- CasADi/IPOPT backend for MPC-ED and MPC-CBF.
- Random shooting vs CasADi/IPOPT comparison with 20 matched seeds by default; use 50 for a larger backend-only paper run.
- Obstacle prediction noise.
- Obstacle speed sweep.
- Horizon/gamma ablation.
- Stress test with 100 seeds.
- Auto-generated tables, figures, and paper-style report section.
- Paired ED-vs-CBF delta table for clearance, path length, solve time, success, and collision.

Key outputs:

```text
results/<experiment_name>/config.yaml
results/<experiment_name>/metrics_summary.csv
results/<experiment_name>/per_seed_metrics.csv
results/<experiment_name>/trajectories/
results/<experiment_name>/figures/
results/<experiment_name>/logs/run.log
results/<experiment_name>/report.md
docs/tables/summary_metrics.md
docs/tables/summary_metrics.csv
docs/tables/scenario_comparison.md
docs/tables/scenario_comparison.csv
docs/tables/paired_delta.md
docs/tables/paired_delta.csv
docs/figures/extended/
docs/paper_section_results.md
```

Selected results:

| Suite | Method | Seeds | Success rate | Collision rate | Mean clearance | Mean solve time |
|---|---|---:|---:|---:|---:|---:|
| Main E4 50-seed | ED | 50 | 0.84 | 0.00 | 0.058 m | 1.823 ms |
| Main E4 50-seed | CBF gamma=0.08 | 50 | 0.86 | 0.00 | 0.823 m | 1.846 ms |
| Stress 100-seed | ED | 100 | 0.89 | 0.00 | 0.054 m | 1.822 ms |
| Stress 100-seed | CBF gamma=0.08 | 100 | 0.81 | 0.00 | 0.824 m | 1.859 ms |
| Backend comparison | CasADi/IPOPT ED | 20 | 0.15 | 0.85 | 0.001 m | 6.004 ms |
| Backend comparison | CasADi/IPOPT CBF gamma=0.08 | 20 | 1.00 | 0.00 | 0.628 m | 5.629 ms |

Backend diagnostic metrics separate optimizer behavior from closed-loop control failure:

| Backend | Method | Seeds | Control failure | Infeasible rate | Fallback rate | Collision after fallback |
|---|---|---:|---:|---:|---:|---:|
| CasADi/IPOPT | ED | 20 | 0.85 | 0.00 | 0.00 | 0.00 |
| CasADi/IPOPT | CBF gamma=0.08 | 20 | 0.00 | 0.00 | 0.00 | 0.00 |

Scenario-level ED vs CBF comparison:

| Scenario | Seeds | ED succ. | CBF succ. | ED coll. | CBF coll. | ED clear. | CBF clear. | Clear. gain | ED time | CBF time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Base | 50 | 0.84 | 0.86 | 0.00 | 0.00 | 0.058 | 0.823 | 0.765 | 5.48 | 6.05 |
| Fast crossing | 50 | 0.90 | 0.64 | 0.00 | 0.00 | 0.054 | 0.656 | 0.602 | 5.59 | 7.57 |
| Late crossing | 50 | 0.92 | 0.94 | 0.00 | 0.00 | 0.036 | 0.798 | 0.762 | 6.14 | 7.24 |
| Large obstacle | 50 | 0.94 | 0.94 | 0.02 | 0.00 | 0.081 | 0.675 | 0.594 | 5.42 | 6.38 |
| Noisy prediction | 50 | 0.90 | 0.46 | 0.04 | 0.00 | 0.085 | 1.071 | 0.986 | 5.60 | 10.18 |
| Short horizon | 50 | 0.96 | 1.00 | 0.04 | 0.00 | 0.004 | 0.628 | 0.624 | 3.89 | 4.40 |

Interpretation:

- CBF consistently increases proactive clearance relative to ED.
- In the base 50-seed matched comparison, CBF improves mean clearance from `0.058 m` to `0.823 m` with similar random-shooting solve time.
- In the 100-seed stress test, CBF keeps high clearance but has lower success, showing the safety-performance trade-off that later adaptive/language methods must address.
- In the 20-seed CasADi/IPOPT backend comparison, CBF reduces collision rate from `0.85` to `0.00`; fallback and collision-after-fallback rates are both `0.00`, so this is a closed-loop control difference rather than a fallback artifact.

## Initial Acceptance Criteria

Block A is ready for GitHub/public baseline use when:

- E0, E2, E3, and E4 can run from scripted commands. Done in v1.
- Each experiment writes a config-linked `summary.json`. Done in v1.
- Each experiment records seed, method, scenario, and solver settings. Done in v1.
- E4 produces trajectory and distance-to-obstacle plots. Done in v1.
- Results can be reproduced without API keys or external LLM services.

## Next Implementation Steps

1. Use the extended Block A tables and figures as the control baseline for Block B and Block C.
2. Carry the same `reproduce_all.sh` + generated tables/figures/report pattern into the next block repo.
3. Add adaptive/language-guided parameter updates in later blocks and compare them against the fixed ED/CBF baselines here.
