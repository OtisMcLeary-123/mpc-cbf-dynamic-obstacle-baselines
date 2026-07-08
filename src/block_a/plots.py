from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .scenario import Scenario, obstacle_position


def plot_trajectory(
    path: str | Path,
    scenario: Scenario,
    traces: dict[str, list[dict[str, Any]]],
) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, rows in traces.items():
        xy = np.array([[float(row["x"]), float(row["y"])] for row in rows])
        ax.plot(xy[:, 0], xy[:, 1], label=label, linewidth=2)

    steps = np.arange(scenario.simulation.max_steps)
    obs = obstacle_position(scenario, steps)
    ax.plot(obs[:, 0], obs[:, 1], "k--", linewidth=1.5, label="obstacle path")
    circle = plt.Circle(
        scenario.obstacle.initial_position,
        scenario.obstacle.radius + scenario.robot.radius,
        color="tab:red",
        alpha=0.18,
        label="collision radius",
    )
    ax.add_patch(circle)
    ax.scatter([scenario.robot.start[0]], [scenario.robot.start[1]], marker="o", c="tab:green", label="start")
    ax.scatter([scenario.robot.target[0]], [scenario.robot.target[1]], marker="*", c="tab:orange", s=130, label="target")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Block A trajectory comparison")
    ax.axis("equal")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_distance(path: str | Path, traces: dict[str, list[dict[str, Any]]]) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for label, rows in traces.items():
        t = [float(row["time"]) for row in rows]
        d = [float(row["clearance"]) for row in rows]
        ax.plot(t, d, label=label, linewidth=2)
    ax.axhline(0.0, color="tab:red", linestyle="--", linewidth=1.5, label="collision boundary")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("clearance to obstacle [m]")
    ax.set_title("Distance to obstacle")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_metric_boxplot(
    path: str | Path,
    grouped_values: dict[str, list[float]],
    ylabel: str,
    title: str,
) -> None:
    labels = [label for label, values in grouped_values.items() if values]
    if not labels:
        return

    values = [grouped_values[label] for label in labels]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.boxplot(values, tick_labels=labels, showmeans=True)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.25)
    for tick in ax.get_xticklabels():
        tick.set_rotation(15)
        tick.set_ha("right")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
