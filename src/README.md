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

The current v1 implementation uses a deterministic NumPy random-shooting MPC controller for reproducible micro-experiments. ED and CBF baselines share the same rollout optimizer and differ only in the safety constraint evaluation:

- ED: Euclidean distance constraint.
- CBF: discrete-time CBF condition `h_{k+1} >= (1 - gamma) h_k`.

The extended implementation also includes an optional CasADi/IPOPT backend for MPC-ED and MPC-CBF. Use `--backend casadi` on E2/E3/E4 scripts.

`artifacts.py` writes the standard Block A result contract consumed by later LaMPC/LLM blocks: `config.yaml`, aggregate/per-seed metric CSVs, per-seed trajectories, figures, logs, and `report.md`.
