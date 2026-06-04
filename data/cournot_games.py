"""Synthetic Cournot competition benchmark from the paper's market experiments."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

EPS = 1e-9


@dataclass
class CournotInstance:
    instance_id: int
    num_firms: int
    intercept: float
    slope: float
    marginal_cost: float
    quantities: list[float]


def equilibrium_quantities(num_firms: int, intercept: float, slope: float, marginal_cost: float) -> np.ndarray:
    if slope >= 0:
        raise ValueError("Cournot slope must be negative")
    q = max((intercept - marginal_cost) / (-(num_firms + 1) * slope), 0.0)
    return np.full(num_firms, q, dtype=float)


def best_response(opponent_total: float, intercept: float, slope: float, marginal_cost: float) -> float:
    candidate = (marginal_cost - intercept - slope * opponent_total) / (2.0 * slope)
    return float(max(candidate, 0.0))


def cournot_exploitability(estimated_cost: float, intercept: float, slope: float, quantities: np.ndarray) -> float:
    total = 0.0
    for i, observed_q in enumerate(quantities):
        opponent_total = float(np.sum(quantities) - observed_q)
        y = best_response(opponent_total, intercept, slope, estimated_cost)
        observed_profit = observed_q * (intercept + slope * np.sum(quantities) - estimated_cost)
        deviation_profit = y * (intercept + slope * (y + opponent_total) - estimated_cost)
        total += deviation_profit - observed_profit
    return float(max(total, 0.0))


def relative_abs(estimated: float, true: float) -> float:
    return float(abs(estimated - true) / max(abs(true), EPS))


def generate_cournot_instances(count: int, seed: int) -> list[CournotInstance]:
    rng = np.random.default_rng(seed)
    instances: list[CournotInstance] = []
    for idx in range(count):
        cost = float(rng.uniform(2.0, 20.0))
        intercept = float(rng.uniform(max(10.0, cost + 1.0), 100.0))
        slope = float(rng.uniform(-10.0, -0.01))
        quantities = equilibrium_quantities(2, intercept, slope, cost)
        instances.append(
            CournotInstance(
                instance_id=idx,
                num_firms=2,
                intercept=intercept,
                slope=slope,
                marginal_cost=cost,
                quantities=quantities.tolist(),
            )
        )
    return instances


def write_jsonl(instances: list[CournotInstance], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for instance in instances:
            handle.write(json.dumps(asdict(instance), sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/cournot_instances.jsonl"))
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=3025)
    args = parser.parse_args()
    write_jsonl(generate_cournot_instances(args.count, args.seed), args.output)


if __name__ == "__main__":
    main()
