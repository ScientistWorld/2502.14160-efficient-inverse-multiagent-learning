"""Synthetic Bertrand oligopoly benchmark from the paper's market experiments."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

EPS = 1e-9


@dataclass
class BertrandInstance:
    instance_id: int
    num_firms: int
    demand_intercept: float
    demand_slope: float
    marginal_cost: float
    prices: list[float]


def market_demand(price: float, intercept: float, slope: float) -> float:
    return float(max(intercept + slope * price, 0.0))


def individual_demand(price: float, opponent_prices: np.ndarray, intercept: float, slope: float) -> float:
    all_prices = np.concatenate(([price], opponent_prices))
    min_price = float(np.min(all_prices))
    if abs(price - min_price) > 1e-8:
        return 0.0
    tied = int(np.sum(np.abs(all_prices - min_price) <= 1e-8))
    return market_demand(min_price, intercept, slope) / tied


def profit(price: float, opponent_prices: np.ndarray, intercept: float, slope: float, cost: float) -> float:
    return individual_demand(price, opponent_prices, intercept, slope) * (price - cost)


def equilibrium_prices(num_firms: int, marginal_cost: float) -> np.ndarray:
    return np.full(num_firms, marginal_cost, dtype=float)


def best_response_price(opponent_price: float, intercept: float, slope: float, cost: float) -> float:
    """Best response in a two-firm homogeneous-good Bertrand game.

    A firm either ties the opponent's price, prices above and sells nothing, or
    undercuts by an arbitrarily small amount.  The undercut branch maximizes the
    monopoly profit subject to price <= opponent_price.  We use a tiny
    deterministic epsilon for the strict undercut, which preserves the same
    inverse-regret computation while keeping artifacts numeric.
    """
    if slope >= 0:
        raise ValueError("Demand slope must be negative")
    eps = 1e-6
    monopoly = (slope * cost - intercept) / (2.0 * slope)
    undercut = min(max(monopoly, 0.0), max(opponent_price - eps, 0.0))
    candidates = [0.0, opponent_price, max(opponent_price + eps, 0.0), undercut]
    values = [profit(p, np.asarray([opponent_price]), intercept, slope, cost) for p in candidates]
    return float(candidates[int(np.argmax(values))])


def bertrand_exploitability(estimated_cost: float, intercept: float, slope: float, prices: np.ndarray) -> float:
    total = 0.0
    for i, observed_price in enumerate(prices):
        opponents = np.delete(prices, i)
        y = best_response_price(float(opponents[0]), intercept, slope, estimated_cost)
        observed_profit = profit(float(observed_price), opponents, intercept, slope, estimated_cost)
        deviation_profit = profit(y, opponents, intercept, slope, estimated_cost)
        total += deviation_profit - observed_profit
    return float(max(total, 0.0))


def relative_abs(estimated: float, true: float) -> float:
    return float(abs(estimated - true) / max(abs(true), EPS))


def generate_bertrand_instances(count: int, seed: int) -> list[BertrandInstance]:
    rng = np.random.default_rng(seed)
    instances: list[BertrandInstance] = []
    for idx in range(count):
        cost = float(rng.uniform(2.0, 20.0))
        intercept = float(rng.uniform(max(10.0, cost + 1.0), 100.0))
        max_negative_slope = min(10.0, (intercept - 0.5) / cost)
        slope = float(-rng.uniform(0.01, max_negative_slope))
        prices = equilibrium_prices(2, cost)
        instances.append(
            BertrandInstance(
                instance_id=idx,
                num_firms=2,
                demand_intercept=intercept,
                demand_slope=slope,
                marginal_cost=cost,
                prices=prices.tolist(),
            )
        )
    return instances


def write_jsonl(instances: list[BertrandInstance], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for instance in instances:
            handle.write(json.dumps(asdict(instance), sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/bertrand_instances.jsonl"))
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=4025)
    args = parser.parse_args()
    write_jsonl(generate_bertrand_instances(args.count, args.seed), args.output)


if __name__ == "__main__":
    main()
