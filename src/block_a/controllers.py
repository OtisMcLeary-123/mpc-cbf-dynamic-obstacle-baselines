from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np

from .dynamics import clip_norm, nominal_pd_control, step_state
from .scenario import Scenario, obstacle_position, predicted_obstacle_position

try:
    import casadi as ca
except ImportError:  # pragma: no cover - exercised when optional dependency is absent.
    ca = None


@dataclass(frozen=True)
class ControlResult:
    control: np.ndarray
    solve_time_ms: float
    solver_success: bool
    predicted_violation: float
    backend: str = "random_shooting"


class SamplingMPCController:
    """Deterministic random-shooting MPC for lightweight baseline experiments."""

    def __init__(
        self,
        scenario: Scenario,
        method: str,
        seed: int,
        gamma: float | None = None,
        obstacle_enabled: bool = True,
    ) -> None:
        if method not in {"smoke", "ed", "cbf"}:
            raise ValueError(f"Unsupported method: {method}")
        self.scenario = scenario
        self.method = method
        self.seed = seed
        self.gamma = gamma
        self.obstacle_enabled = obstacle_enabled

    @property
    def safe_radius(self) -> float:
        return self.scenario.robot.radius + self.scenario.obstacle.radius

    def solve(self, state: np.ndarray, step: int) -> ControlResult:
        start = time.perf_counter()
        if self.method == "smoke" and not self.obstacle_enabled:
            control = nominal_pd_control(state, self.scenario)
            solve_time_ms = (time.perf_counter() - start) * 1000.0
            return ControlResult(
                control=control,
                solve_time_ms=solve_time_ms,
                solver_success=True,
                predicted_violation=0.0,
            )
        controls = self._candidate_sequences(state, step)
        cost, violation = self._score_sequences(state, controls, step)
        best_idx = int(np.argmin(cost))
        solve_time_ms = (time.perf_counter() - start) * 1000.0
        return ControlResult(
            control=controls[best_idx, 0],
            solve_time_ms=solve_time_ms,
            solver_success=bool(violation[best_idx] <= 1e-7),
            predicted_violation=float(violation[best_idx]),
        )

    def _candidate_sequences(self, state: np.ndarray, step: int) -> np.ndarray:
        sim = self.scenario.simulation
        robot = self.scenario.robot
        rng = np.random.default_rng(self.seed * 10007 + step * 97 + 13)
        horizon = sim.horizon_steps
        n = sim.candidate_sequences
        nominal = nominal_pd_control(state, self.scenario)

        controls = rng.normal(loc=nominal, scale=0.95, size=(n, horizon, 2))
        decay = np.linspace(1.0, 0.45, horizon)[None, :, None]
        controls = nominal + (controls - nominal) * decay

        controls[0, :, :] = nominal
        lateral = self._lateral_direction(state, step)
        for idx, scale in enumerate([0.7, 1.1, -0.7, -1.1], start=1):
            if idx < n:
                controls[idx, :, :] = nominal + scale * lateral * robot.max_accel
        return clip_norm(controls, robot.max_accel)

    def _lateral_direction(self, state: np.ndarray, step: int) -> np.ndarray:
        pos = state[:2]
        obs = obstacle_position(self.scenario, step)
        to_target = self.scenario.robot.target - pos
        direction = np.array([-to_target[1], to_target[0]], dtype=float)
        if np.linalg.norm(direction) < 1e-9:
            direction = np.array([0.0, 1.0])
        direction = direction / np.linalg.norm(direction)
        if np.dot(obs - pos, direction) > 0:
            direction = -direction
        return direction

    def _score_sequences(
        self, state: np.ndarray, controls: np.ndarray, step: int
    ) -> tuple[np.ndarray, np.ndarray]:
        scenario = self.scenario
        target = scenario.robot.target
        states = np.repeat(state[None, :], controls.shape[0], axis=0)
        cost = np.zeros(controls.shape[0])
        violation_total = np.zeros(controls.shape[0])
        previous_h = self._barrier_value(
            states[:, :2], predicted_obstacle_position(scenario, step, seed=self.seed)
        )

        for horizon_idx in range(scenario.simulation.horizon_steps):
            u = controls[:, horizon_idx, :]
            states = step_state(states, u, scenario)
            pos = states[:, :2]
            vel = states[:, 2:]
            target_error = pos - target
            cost += 1.0 * np.sum(target_error * target_error, axis=1)
            cost += 0.05 * np.sum(vel * vel, axis=1)
            cost += 0.02 * np.sum(u * u, axis=1)

            if self.obstacle_enabled:
                obs = predicted_obstacle_position(
                    scenario, step + horizon_idx + 1, seed=self.seed
                )
                h_value = self._barrier_value(pos, obs)
                if self.method == "ed":
                    violation = np.maximum(0.0, -h_value)
                elif self.method == "cbf":
                    gamma = 1.0 if self.gamma is None else float(self.gamma)
                    cbf_rhs = (1.0 - gamma) * previous_h
                    violation = np.maximum(0.0, cbf_rhs - h_value)
                    violation += 5.0 * np.maximum(0.0, -h_value)
                    previous_h = h_value
                else:
                    violation = np.zeros_like(h_value)
                violation_total += violation
                cost += 9000.0 * violation * violation + 2000.0 * violation

        final_error = states[:, :2] - target
        cost += 12.0 * np.sum(final_error * final_error, axis=1)
        return cost, violation_total

    def _barrier_value(self, positions: np.ndarray, obstacle: np.ndarray) -> np.ndarray:
        delta = positions - obstacle
        return np.sum(delta * delta, axis=-1) - self.safe_radius * self.safe_radius


class CasadiMPCController:
    """Small CasADi/IPOPT MPC backend for ED and CBF comparisons."""

    def __init__(
        self,
        scenario: Scenario,
        method: str,
        seed: int,
        gamma: float | None = None,
        obstacle_enabled: bool = True,
        horizon_steps: int | None = None,
    ) -> None:
        if ca is None:
            raise RuntimeError("CasADi is not installed. Install with `python3 -m pip install casadi`.")
        if method not in {"ed", "cbf"}:
            raise ValueError("CasADi backend currently supports `ed` and `cbf` only.")
        self.scenario = scenario
        self.method = method
        self.seed = seed
        self.gamma = 0.08 if gamma is None else float(gamma)
        self.obstacle_enabled = obstacle_enabled
        self.horizon_steps = min(int(horizon_steps or scenario.simulation.horizon_steps), 10)
        self._build_solver()

    @property
    def safe_radius(self) -> float:
        return self.scenario.robot.radius + self.scenario.obstacle.radius

    def _build_solver(self) -> None:
        scenario = self.scenario
        n = self.horizon_steps
        dt = scenario.simulation.dt
        self.opti = ca.Opti()
        self.x = self.opti.variable(4, n + 1)
        self.u = self.opti.variable(2, n)
        self.x0 = self.opti.parameter(4)
        self.obs = self.opti.parameter(2, n + 1)

        target = scenario.robot.target
        self.opti.subject_to(self.x[:, 0] == self.x0)
        objective = 0
        for k in range(n):
            px = self.x[0, k]
            py = self.x[1, k]
            vx = self.x[2, k]
            vy = self.x[3, k]
            ax = self.u[0, k]
            ay = self.u[1, k]
            self.opti.subject_to(self.x[0, k + 1] == px + vx * dt + 0.5 * ax * dt * dt)
            self.opti.subject_to(self.x[1, k + 1] == py + vy * dt + 0.5 * ay * dt * dt)
            self.opti.subject_to(self.x[2, k + 1] == vx + ax * dt)
            self.opti.subject_to(self.x[3, k + 1] == vy + ay * dt)
            self.opti.subject_to(self.opti.bounded(-scenario.robot.max_accel, ax, scenario.robot.max_accel))
            self.opti.subject_to(self.opti.bounded(-scenario.robot.max_accel, ay, scenario.robot.max_accel))
            self.opti.subject_to(self.opti.bounded(-scenario.robot.max_speed, self.x[2, k + 1], scenario.robot.max_speed))
            self.opti.subject_to(self.opti.bounded(-scenario.robot.max_speed, self.x[3, k + 1], scenario.robot.max_speed))

            objective += 1.0 * ((self.x[0, k + 1] - target[0]) ** 2 + (self.x[1, k + 1] - target[1]) ** 2)
            objective += 0.03 * (ax**2 + ay**2)

            if self.obstacle_enabled:
                h_next = self._casadi_h(self.x[0:2, k + 1], self.obs[:, k + 1])
                if self.method == "ed":
                    self.opti.subject_to(h_next >= 0)
                else:
                    h_now = self._casadi_h(self.x[0:2, k], self.obs[:, k])
                    self.opti.subject_to(h_next >= (1.0 - self.gamma) * h_now)
                    self.opti.subject_to(h_next >= 0)

        objective += 10.0 * ((self.x[0, n] - target[0]) ** 2 + (self.x[1, n] - target[1]) ** 2)
        self.opti.minimize(objective)
        options = {
            "print_time": False,
            "ipopt.print_level": 0,
            "ipopt.max_iter": 80,
            "ipopt.sb": "yes",
            "ipopt.acceptable_tol": 1e-5,
        }
        self.opti.solver("ipopt", options)

    def _casadi_h(self, position, obstacle):
        dx = position[0] - obstacle[0]
        dy = position[1] - obstacle[1]
        return dx * dx + dy * dy - self.safe_radius * self.safe_radius

    def solve(self, state: np.ndarray, step: int) -> ControlResult:
        start = time.perf_counter()
        try:
            obs = np.stack(
                [
                    predicted_obstacle_position(self.scenario, step + k, seed=self.seed)
                    for k in range(self.horizon_steps + 1)
                ],
                axis=1,
            )
            self.opti.set_value(self.x0, state)
            self.opti.set_value(self.obs, obs)
            nominal = nominal_pd_control(state, self.scenario)
            self.opti.set_initial(self.u, np.tile(nominal.reshape(2, 1), (1, self.horizon_steps)))
            self.opti.set_initial(self.x, np.tile(state.reshape(4, 1), (1, self.horizon_steps + 1)))
            sol = self.opti.solve()
            control = np.array(sol.value(self.u[:, 0]), dtype=float).reshape(2)
            success = True
            violation = 0.0
        except Exception:
            control = nominal_pd_control(state, self.scenario)
            success = False
            violation = 1.0
        solve_time_ms = (time.perf_counter() - start) * 1000.0
        return ControlResult(
            control=clip_norm(control[None, :], self.scenario.robot.max_accel)[0],
            solve_time_ms=solve_time_ms,
            solver_success=success,
            predicted_violation=violation,
            backend="casadi_ipopt",
        )
