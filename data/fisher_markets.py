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
    """Return prices and allocation for a two-good linear-utility Fisher market.

    With two goods, equilibrium prices are pinned down by a marginal buyer's
    value ratio. Buyers with larger value ratios spend on good 0, buyers with
    smaller ratios spend on good 1, and the marginal ratio group splits to clear
    both unit supplies.
    """
    num_buyers, num_goods = types.shape
    if num_goods != 2:
        raise ValueError("linear_equilibrium currently supports exactly two goods")

    ratios = types[:, 0] / np.maximum(types[:, 1], EPS)
    total_budget = float(np.sum(budgets))

    order = np.argsort(-ratios)
    sorted_ratios = ratios[order]
    sorted_budgets = budgets[order]
    cumulative = np.cumsum(sorted_budgets)
    for split in range(1, num_buyers):
        high_budget = float(cumulative[split - 1])
        low_budget = total_budget - high_budget
        if low_budget <= EPS:
            continue
        ratio = high_budget / low_budget
        if sorted_ratios[split - 1] + 1e-10 >= ratio >= sorted_ratios[split] - 1e-10:
            prices = np.asarray([high_budget, low_budget], dtype=float)
            allocation = np.zeros((num_buyers, num_goods), dtype=float)
            high_indices = order[:split]
            low_indices = order[split:]
            allocation[high_indices, 0] = budgets[high_indices] / np.maximum(prices[0], EPS)
            allocation[low_indices, 1] = budgets[low_indices] / np.maximum(prices[1], EPS)
            return prices, allocation

    for ratio in sorted(set(float(r) for r in ratios), reverse=True):
        high = ratios > ratio + 1e-10
        tied = np.abs(ratios - ratio) <= 1e-10
        high_budget = float(np.sum(budgets[high]))
        tied_budget = float(np.sum(budgets[tied]))
        price0 = total_budget * ratio / (1.0 + ratio)
        if high_budget - 1e-8 <= price0 <= high_budget + tied_budget + 1e-8:
            prices = np.asarray([price0, total_budget - price0], dtype=float)
            allocation = np.zeros((num_buyers, num_goods), dtype=float)
            allocation[high, 0] = budgets[high] / np.maximum(prices[0], EPS)
            low = ratios < ratio - 1e-10
            allocation[low, 1] = budgets[low] / np.maximum(prices[1], EPS)

            needed_tied_spend0 = min(max(price0 - high_budget, 0.0), tied_budget)
            tied_indices = np.where(tied)[0]
            for buyer in tied_indices:
                spend0 = needed_tied_spend0 * budgets[buyer] / max(tied_budget, EPS)
                spend1 = budgets[buyer] - spend0
                allocation[buyer, 0] = spend0 / np.maximum(prices[0], EPS)
                allocation[buyer, 1] = spend1 / np.maximum(prices[1], EPS)
            return prices, allocation

    raise RuntimeError("Could not construct two-good linear Fisher equilibrium")


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
