# Source

This directory will contain the shared Block A implementation.

Modules:

```text
dynamics.py
scenario.py
metrics.py
controllers.py
runner.py
artifacts.py
plots.py
```

The implementation contains two MPC backends:

- `random_shooting`: deterministic NumPy random-shooting MPC for fast reproducible sweeps.
- `casadi`: CasADi/IPOPT nonlinear-programming backend for ED-vs-CBF solver-level comparison.

ED and CBF baselines share the selected backend and differ only in the safety constraint evaluation:

- ED: Euclidean distance constraint.
- CBF: discrete-time CBF condition `h_{k+1} >= (1 - gamma) h_k`.

Use `--backend random_shooting` or `--backend casadi` on E2/E3/E4 scripts. CasADi/IPOPT is slower but is the backend used for the 20-seed collision-reduction comparison.

Control traces distinguish optimizer and closed-loop outcomes:

- `solver_success`: optimizer returned a usable control.
- `infeasible`: no feasible candidate/plan was available at that step.
- `fallback_used`: nominal fallback control was used after solver failure.
- `control_failure`: the run failed to complete safely, independent of solver status.

`artifacts.py` writes the standard Block A result contract consumed by later LaMPC/LLM blocks: `config.yaml`, aggregate/per-seed metric CSVs, per-seed trajectories, figures, logs, and `report.md`.
