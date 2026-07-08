# Block A: Control Baselines

## Goal

This repository contains the first reproducible block of the LaMPC-CBF reference micro-experiments.

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
solver_failure_rate
```

## Repository Structure

```text
configs/   scenario and experiment configs
docs/      experiment protocol, reports, and log
results/   generated summaries, traces, and plots
scripts/   runner and plotting entrypoints
src/       shared implementation
```

## Initial Acceptance Criteria

Block A is ready for GitHub/public baseline use when:

- E0, E2, E3, and E4 can run from scripted commands.
- Each experiment writes a config-linked `summary.json`.
- Each experiment records seed, method, scenario, and solver settings.
- E4 produces trajectory and distance-to-obstacle plots.
- Results can be reproduced without API keys or external LLM services.

## Next Implementation Steps

1. Implement the 2D point-mass dynamics and shared scenario loader.
2. Implement E0 solver smoke test.
3. Implement E2 MPC-ED baseline.
4. Implement E3 MPC-CBF gamma sweep.
5. Implement E4 ED-vs-CBF comparison script and report.
