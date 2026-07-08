# Block A Results Section Draft

## Experimental Setup

We evaluate MPC with Euclidean-distance constraints and MPC-CBF on a 2D point-mass dynamic obstacle navigation benchmark. All comparisons use matched seeds within each scenario. Metrics include success rate, collision rate, minimum clearance, path length, completion time, and solve time.

The extended benchmark includes the base scenario, six harder dynamic-obstacle scenarios, obstacle prediction noise, obstacle speed sweeps, horizon/gamma ablations, a 100-seed stress test, and a backend comparison between the lightweight random-shooting MPC and a CasADi/IPOPT nonlinear-programming backend.

## Main Matched-Seed Comparison

In the 50-seed base-scenario ED-vs-CBF comparison, ED achieved success rate 0.840 with collision rate 0.000 and mean minimum clearance 0.058 m. MPC-CBF with `gamma=0.08` achieved success rate 0.860 with collision rate 0.000 and mean minimum clearance 0.823 m. Mean solve times were 1.823 ms for ED and 1.846 ms for CBF. Fallback rates were 0.000 for ED and 0.000 for CBF; collision-after-fallback rates were 0.000 and 0.000, respectively.

These results support the intended Block A role: CBF is not merely a collision-avoidance constraint, but a more proactive safety constraint that increases clearance before the robot reaches the obstacle boundary.

## Stress Test

In the 100-seed stress test, ED achieved success rate 0.890 with collision rate 0.000 and mean minimum clearance 0.054 m. MPC-CBF with `gamma=0.08` achieved success rate 0.810 with collision rate 0.000 and mean minimum clearance 0.824 m. Mean solve times were 1.822 ms for ED and 1.859 ms for CBF. Fallback rates were 0.000 for ED and 0.000 for CBF; collision-after-fallback rates were 0.000 and 0.000, respectively.

This exposes the safety-performance trade-off: fixed-gamma CBF maintains a much larger safety margin but can reduce task completion under harder seeded conditions.

## Backend Comparison

In the 20-seed CasADi/IPOPT backend comparison, ED achieved success rate 0.150 with collision rate 0.850 and mean minimum clearance 0.001 m. MPC-CBF with `gamma=0.08` achieved success rate 1.000 with collision rate 0.000 and mean minimum clearance 0.628 m. Mean solve times were 6.004 ms for ED and 5.629 ms for CBF. Fallback rates were 0.000 for ED and 0.000 for CBF; collision-after-fallback rates were 0.000 and 0.000, respectively.

The CasADi/IPOPT table reports solver failure separately from control failure, including infeasible, fallback, and collision-after-fallback rates. This separates numerical optimization issues from actual closed-loop collision outcomes.

In the 20-seed random-shooting backend comparison, ED achieved success rate 0.900 with collision rate 0.000 and mean minimum clearance 0.077 m. MPC-CBF with `gamma=0.08` achieved success rate 0.850 with collision rate 0.000 and mean minimum clearance 0.838 m. Mean solve times were 1.831 ms for ED and 1.870 ms for CBF. Fallback rates were 0.000 for ED and 0.000 for CBF; collision-after-fallback rates were 0.000 and 0.000, respectively.

The random-shooting backend remains useful for fast sweeps and stress tests; CasADi/IPOPT is slower but closer to the optimization stack used in the reference implementation.

## Ablations

The horizon/gamma ablation confirms that smaller `gamma` generally increases clearance. Shorter horizons reduce solve time, but the safety-performance behavior depends on the obstacle timing and scenario geometry.

The obstacle-speed and prediction-noise sweeps show that CBF can become overly conservative under high uncertainty: clearance remains high, but completion rate can drop. This motivates Block B and later language-interface experiments, where adaptive policies should preserve safety without sacrificing completion.

## Tables

See `docs/tables/summary_metrics.md` for mean, standard deviation, and 95% confidence intervals. See `docs/tables/scenario_comparison.md` for a scenario-by-scenario ED-vs-CBF table. See `docs/tables/paired_delta.md` for matched-seed paired deltas.

## Standard Artifacts

Every new experiment output also writes `config.yaml`, `metrics_summary.csv`, fixed-schema `per_seed_metrics.csv`, per-seed trajectory CSVs, figures, logs, and `report.md` for downstream LaMPC/LLM blocks.

## Reproducibility

Run `scripts/reproduce_all.sh` to regenerate the extended benchmark outputs, tables, figures, and this report draft.
