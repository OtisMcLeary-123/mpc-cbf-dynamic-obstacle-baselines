# Block A Results Section Draft

## Experimental Setup

We evaluate MPC with Euclidean-distance constraints and MPC-CBF on a 2D point-mass dynamic obstacle navigation benchmark. All comparisons use matched seeds within each scenario. Metrics include success rate, collision rate, minimum clearance, path length, completion time, and solve time.

The extended benchmark includes the base scenario, six harder dynamic-obstacle scenarios, obstacle prediction noise, obstacle speed sweeps, horizon/gamma ablations, a 100-seed stress test, and a backend comparison between the lightweight random-shooting MPC and a CasADi/IPOPT nonlinear-programming backend.

## Main Matched-Seed Comparison

In the 50-seed base-scenario ED-vs-CBF comparison, ED achieved a success rate of 0.84 with zero collisions and a mean minimum clearance of 0.058 m. MPC-CBF with `gamma=0.08` achieved a success rate of 0.86 with zero collisions and a substantially larger mean minimum clearance of 0.823 m. Mean solve times were similar: 1.825 ms for ED and 1.851 ms for CBF under the random-shooting backend.

These results support the intended Block A role: CBF is not merely a collision-avoidance constraint, but a more proactive safety constraint that increases clearance before the robot reaches the obstacle boundary.

## Stress Test

In the 100-seed stress test, ED achieved a success rate of 0.89 with mean clearance 0.054 m, while CBF achieved success rate 0.81 with mean clearance 0.824 m. This exposes the safety-performance trade-off: fixed-gamma CBF maintains a much larger safety margin but can reduce task completion under harder seeded conditions.

## Backend Comparison

The CasADi/IPOPT backend was implemented for both MPC-ED and MPC-CBF. In the small matched-seed backend comparison, CasADi/IPOPT ED achieved success rate 0.20 and collision rate 0.80, while CasADi/IPOPT CBF achieved success rate 1.00 and collision rate 0.00. This mirrors the qualitative claim from the reference paper: distance constraints can ride the obstacle boundary, while CBF constraints enforce more proactive avoidance.

The random-shooting backend remains useful for fast sweeps and stress tests; CasADi/IPOPT is slower but closer to the optimization stack used in the reference implementation.

## Ablations

The horizon/gamma ablation confirms that smaller `gamma` generally increases clearance. Shorter horizons reduce solve time, but the safety-performance behavior depends on the obstacle timing and scenario geometry.

The obstacle-speed and prediction-noise sweeps show that CBF can become overly conservative under high uncertainty: clearance remains high, but completion rate can drop. This motivates Block B and later language-interface experiments, where adaptive policies should preserve safety without sacrificing completion.

## Tables

See `docs/tables/summary_metrics.md` for mean, standard deviation, and 95% confidence intervals. See `docs/tables/scenario_comparison.md` for a scenario-by-scenario ED-vs-CBF table.

## Standard Artifacts

Every new experiment output also writes `config.yaml`, `metrics_summary.csv`, fixed-schema `per_seed_metrics.csv`, per-seed trajectory CSVs, figures, logs, and `report.md` for downstream LaMPC/LLM blocks.

## Reproducibility

Run `scripts/reproduce_all.sh` to regenerate the extended benchmark outputs, tables, figures, and this report draft.
