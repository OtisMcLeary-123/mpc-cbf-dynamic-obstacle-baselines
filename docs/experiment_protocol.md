# Block A Experiment Protocol

## Purpose

Block A establishes the no-language control baselines for the paper.

The experiments must use the same scenario, seeds, metrics, and output schema so later language-interface repos can compare against them without changing the control benchmark.

## Experiment Order

```text
E0 -> E2 -> E3 -> E4
```

Extended paper-level order:

```text
hard scenarios -> 50-seed ED vs CBF -> CI tables -> figures
-> CasADi/IPOPT backend -> backend comparison -> prediction noise
-> obstacle speed sweep -> horizon/gamma ablation -> 100-seed stress test
```

## Required Outputs

Each experiment should write:

```text
results/exp_<id>/summary.json
results/exp_<id>/trace.csv
results/exp_<id>/trajectory.png
results/exp_<id>/distance_to_obstacle.png
docs/exp_<id>_report.md
```

## Comparison Rules

- Use the same start, target, obstacle trajectory, and seed list for E2, E3, and E4.
- Do not introduce language feedback, rule-based gamma adaptation, or LLM calls in Block A.
- E3 may sweep fixed gamma values only.
- E4 must compare ED and CBF using matched seeds.

## Acceptance Criteria

- E0 confirms the solver can track the target without obstacles.
- E2 produces a measurable ED safety baseline.
- E3 produces a gamma sweep with collision and min-distance metrics.
- E4 produces a direct ED-vs-CBF comparison table and plots.

## Extended Benchmark Requirements

- Hard scenarios live in `configs/scenarios/`.
- Main paper comparison uses 50 matched seeds.
- Stress test uses 100 matched seeds.
- Tables must report mean, standard deviation, and 95% confidence intervals.
- Figures must include trajectory overlays and clearance curves.
- CasADi/IPOPT backend must be compared against random shooting on matched seeds.
- `scripts/reproduce_all.sh` regenerates extended outputs, tables, figures, and report draft.
