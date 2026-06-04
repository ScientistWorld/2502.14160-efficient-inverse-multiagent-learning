"""Synthetic static Fisher market benchmark used by the reproduction.

The paper's static Fisher experiments use 3 buyers and 2 goods with random
budgets and utility types.  This module creates the problem instances and
contains market-side utilities that are shared by methods, baselines, and
evaluators.  It does not import from method/.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


EPS = 1e-9


@dataclass
class FisherInstance:
    instance_id: int
    utility: str
    types: list[list[float]]
    budgets: list[float]
    prices: list[float]
    allocation: list[list[float]]


def cobb_douglas_equilibrium(types: np.ndarray, budgets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return competitive prices and allocation for normalized CD exponents."""
    shares = types / np.maximum(types.sum(axis=1, keepdims=True), EPS)
    prices = budgets @ shares
    allocation = budgets[:, None] * shares / np.maximum(prices[None, :], EPS)
    return prices, allocation


def linear_equilibrium(types: np.ndarray, budgets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return prices and allocation for a linear-utility Fisher market."""
    from scipy.optimize import minimize

    num_buyers, num_goods = types.shape
    x0 = np.full((num_buyers, num_goods), 1.0 / num_buyers, dtype=float).ravel()

    def objective(flat: np.ndarray) -> float:
        allocation = flat.reshape(num_buyers, num_goods)
        utilities = np.sum(types * allocation, axis=1)
        return float(-np.sum(budgets * np.log(np.maximum(utilities, EPS))))

    constraints = [
        {
            "type": "ineq",
            "fun": lambda flat, good=good: 1.0 - np.sum(flat.reshape(num_buyers, num_goods)[:, good]),
        }
        for good in range(num_goods)
    ]
    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=[(0.0, None)] * x0.size,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(f"Linear Fisher equilibrium solve failed: {result.message}")

    allocation = np.maximum(result.x.reshape(num_buyers, num_goods), 0.0)
    for good in range(num_goods):
        total = float(np.sum(allocation[:, good]))
        if total > 1.0:
            allocation[:, good] /= total

    utilities = np.maximum(np.sum(types * allocation, axis=1), EPS)
    prices = np.zeros(num_goods, dtype=float)
    for good in range(num_goods):
        active = allocation[:, good] > 1e-7
        if np.any(active):
            prices[good] = float(np.mean(budgets[active] * types[active, good] / utilities[active]))
        else:
            prices[good] = float(np.max(budgets * types[:, good] / utilities))
    return prices, allocation


def log_cd_utility(allocation: np.ndarray, types: np.ndarray) -> np.ndarray:
    shares = types / np.maximum(types.sum(axis=1, keepdims=True), EPS)
    return np.sum(shares * np.log(np.maximum(allocation, EPS)), axis=1)


def cd_best_response(budgets: np.ndarray, types: np.ndarray, prices: np.ndarray) -> np.ndarray:
    shares = types / np.maximum(types.sum(axis=1, keepdims=True), EPS)
    return budgets[:, None] * shares / np.maximum(prices[None, :], EPS)


def cd_regret(
    budgets: np.ndarray,
    types: np.ndarray,
    prices: np.ndarray,
    observed_allocation: np.ndarray,
) -> float:
    """Exact EG regret max_Y f(p*,Y;b)-f(p*,X*;b) for CD utilities."""
    best = cd_best_response(budgets, types, prices)
    value_gap = budgets * (log_cd_utility(best, types) - log_cd_utility(observed_allocation, types))
    price_gap = np.sum(prices * (observed_allocation.sum(axis=0) - best.sum(axis=0)))
    return float(np.sum(value_gap) + price_gap)


def log_linear_utility(allocation: np.ndarray, types: np.ndarray) -> np.ndarray:
    return np.log(np.maximum(np.sum(types * allocation, axis=1), EPS))


def linear_best_response(budgets: np.ndarray, types: np.ndarray, prices: np.ndarray) -> np.ndarray:
    bang_per_buck = types / np.maximum(prices[None, :], EPS)
    chosen_goods = np.argmax(bang_per_buck, axis=1)
    allocation = np.zeros_like(types, dtype=float)
    for buyer, good in enumerate(chosen_goods):
        allocation[buyer, good] = budgets[buyer] / max(prices[good], EPS)
    return allocation


def linear_regret(
    budgets: np.ndarray,
    types: np.ndarray,
    prices: np.ndarray,
    observed_allocation: np.ndarray,
) -> float:
    best = linear_best_response(budgets, types, prices)
    value_gap = budgets * (log_linear_utility(best, types) - log_linear_utility(observed_allocation, types))
    price_gap = np.sum(prices * (observed_allocation.sum(axis=0) - best.sum(axis=0)))
    return float(max(np.sum(value_gap) + price_gap, 0.0))


def fisher_regret(
    utility: str,
    budgets: np.ndarray,
    types: np.ndarray,
    prices: np.ndarray,
    observed_allocation: np.ndarray,
) -> float:
    if utility == "cobb_douglas":
        return cd_regret(budgets, types, prices, observed_allocation)
    if utility == "linear":
        return linear_regret(budgets, types, prices, observed_allocation)
    raise ValueError(f"Unsupported utility: {utility}")


def relative_l2(estimated: np.ndarray, true: np.ndarray) -> float:
    return float(np.linalg.norm((estimated - true) / np.maximum(np.abs(true), EPS)))


def generate_cd_instances(count: int, seed: int) -> list[FisherInstance]:
    rng = np.random.default_rng(seed)
    instances: list[FisherInstance] = []
    for idx in range(count):
        raw_types = rng.uniform(0.1, 10.0, size=(3, 2))
        types = raw_types / raw_types.sum(axis=1, keepdims=True)
        budgets = rng.uniform(0.1, 10.0, size=3)
        prices, allocation = cobb_douglas_equilibrium(types, budgets)
        instances.append(
            FisherInstance(
                instance_id=idx,
                utility="cobb_douglas",
                types=types.tolist(),
                budgets=budgets.tolist(),
                prices=prices.tolist(),
                allocation=allocation.tolist(),
            )
        )
    return instances


def generate_linear_instances(count: int, seed: int) -> list[FisherInstance]:
    rng = np.random.default_rng(seed)
    instances: list[FisherInstance] = []
    for idx in range(count):
        types = rng.uniform(0.1, 10.0, size=(3, 2))
        budgets = rng.uniform(0.1, 10.0, size=3)
        prices, allocation = linear_equilibrium(types, budgets)
        instances.append(
            FisherInstance(
                instance_id=idx,
                utility="linear",
                types=types.tolist(),
                budgets=budgets.tolist(),
                prices=prices.tolist(),
                allocation=allocation.tolist(),
            )
        )
    return instances


def write_jsonl(instances: list[FisherInstance], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for instance in instances:
            handle.write(json.dumps(asdict(instance), sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def ensure_dataset(path: Path, count: int = 100, seed: int = 2025) -> None:
    if not path.exists():
        write_jsonl(generate_cd_instances(count=count, seed=seed), path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/fisher_cd_budget_instances.jsonl"))
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2025)
    parser.add_argument("--utility", choices=["cobb_douglas", "linear"], default="cobb_douglas")
    args = parser.parse_args()
    if args.utility == "cobb_douglas":
        instances = generate_cd_instances(args.count, args.seed)
    else:
        instances = generate_linear_instances(args.count, args.seed)
    write_jsonl(instances, args.output)


if __name__ == "__main__":
    main()
