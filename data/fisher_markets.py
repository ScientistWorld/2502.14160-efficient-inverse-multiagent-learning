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


def leontief_equilibrium(types: np.ndarray, budgets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return prices and allocation for a two-good Leontief Fisher market.

    For u_i(x_i)=min_j x_ij/t_ij, buyer i demands the fixed-proportion bundle
    z_i t_i where z_i=b_i/(p dot t_i).  With unit supplies and positive prices,
    prices sum to total budget, so a two-good market reduces to finding p_0 in
    [0, sum_i b_i] such that aggregate good-0 demand equals one.
    """
    if types.shape[1] != 2:
        raise ValueError("leontief_equilibrium currently supports exactly two goods")

    total_budget = float(np.sum(budgets))
    if np.sum(budgets * types[:, 1] / np.maximum(total_budget * types[:, 0], EPS)) <= 1.0 + 1e-10:
        prices = np.asarray([total_budget, 0.0], dtype=float)
        utilities = budgets / np.maximum(types @ prices, EPS)
        return prices, utilities[:, None] * types
    if np.sum(budgets * types[:, 0] / np.maximum(total_budget * types[:, 1], EPS)) <= 1.0 + 1e-10:
        prices = np.asarray([0.0, total_budget], dtype=float)
        utilities = budgets / np.maximum(types @ prices, EPS)
        return prices, utilities[:, None] * types

    lo = 1e-10 * total_budget
    hi = (1.0 - 1e-10) * total_budget

    def excess(price0: float) -> float:
        prices = np.asarray([price0, total_budget - price0], dtype=float)
        denom = np.maximum(types @ prices, EPS)
        demand0 = np.sum(budgets * types[:, 0] / denom)
        return float(demand0 - 1.0)

    # The excess function is continuous but not guaranteed monotone for mixed
    # type ratios, so locate all sign-changing intervals and refine the best.
    grid = np.linspace(lo, hi, 2049)
    values = np.asarray([excess(float(x)) for x in grid])
    best_price0 = float(grid[int(np.argmin(np.abs(values)))])
    best_abs = float(np.min(np.abs(values)))

    for left, right, f_left, f_right in zip(grid[:-1], grid[1:], values[:-1], values[1:]):
        if abs(float(f_left)) < best_abs:
            best_price0 = float(left)
            best_abs = abs(float(f_left))
        if f_left == 0.0:
            continue
        if f_left * f_right > 0.0:
            continue
        a = float(left)
        b = float(right)
        fa = float(f_left)
        for _ in range(80):
            mid = 0.5 * (a + b)
            fm = excess(mid)
            if abs(fm) < best_abs:
                best_price0 = mid
                best_abs = abs(fm)
            if fa * fm <= 0.0:
                b = mid
            else:
                a = mid
                fa = fm

    prices = np.asarray([best_price0, total_budget - best_price0], dtype=float)
    utilities = budgets / np.maximum(types @ prices, EPS)
    allocation = utilities[:, None] * types
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


def log_leontief_utility(allocation: np.ndarray, types: np.ndarray) -> np.ndarray:
    return np.log(np.maximum(np.min(allocation / np.maximum(types, EPS), axis=1), EPS))


def leontief_best_response(budgets: np.ndarray, types: np.ndarray, prices: np.ndarray) -> np.ndarray:
    bundle_costs = np.sum(prices[None, :] * types, axis=1)
    utilities = budgets / np.maximum(bundle_costs, EPS)
    return utilities[:, None] * types


def leontief_regret(
    budgets: np.ndarray,
    types: np.ndarray,
    prices: np.ndarray,
    observed_allocation: np.ndarray,
) -> float:
    best = leontief_best_response(budgets, types, prices)
    value_gap = budgets * (log_leontief_utility(best, types) - log_leontief_utility(observed_allocation, types))
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
    if utility == "leontief":
        return leontief_regret(budgets, types, prices, observed_allocation)
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


def generate_leontief_instances(count: int, seed: int) -> list[FisherInstance]:
    rng = np.random.default_rng(seed)
    instances: list[FisherInstance] = []
    for idx in range(count):
        types = rng.uniform(0.1, 10.0, size=(3, 2))
        budgets = rng.uniform(0.1, 10.0, size=3)
        prices, allocation = leontief_equilibrium(types, budgets)
        instances.append(
            FisherInstance(
                instance_id=idx,
                utility="leontief",
                types=types.tolist(),
                budgets=budgets.tolist(),
                prices=prices.tolist(),
                allocation=allocation.tolist(),
            )
        )
    return instances


NOISY_NUM_SAMPLES = 16
NOISY_LOG_SIGMA = 0.3


def generate_cd_noisy_instances(
    count: int,
    seed: int,
    num_samples: int = NOISY_NUM_SAMPLES,
    log_sigma: float = NOISY_LOG_SIGMA,
) -> list[dict]:
    """Cobb-Douglas markets observed through noisy samples of equilibrium demand.

    Each market is generated exactly like ``generate_cd_instances``.  The
    observer sees the posted equilibrium prices exactly, but only
    ``num_samples`` independent noisy measurements of the equilibrium
    allocation: ``x_sample = x_eq * exp(log_sigma * N(0, 1))`` entrywise.
    The exact equilibrium allocation and the budgets are ground truth.
    """
    rng = np.random.default_rng(seed)
    instances: list[dict] = []
    for idx in range(count):
        raw_types = rng.uniform(0.1, 10.0, size=(3, 2))
        types = raw_types / raw_types.sum(axis=1, keepdims=True)
        budgets = rng.uniform(0.1, 10.0, size=3)
        prices, allocation = cobb_douglas_equilibrium(types, budgets)
        noise = rng.normal(0.0, log_sigma, size=(num_samples,) + allocation.shape)
        samples = allocation[None, :, :] * np.exp(noise)
        instances.append(
            {
                "instance_id": idx,
                "utility": "cobb_douglas",
                "types": types.tolist(),
                "budgets": budgets.tolist(),
                "prices": prices.tolist(),
                "allocation": allocation.tolist(),
                "allocation_samples": samples.tolist(),
            }
        )
    return instances


def write_jsonl(instances: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for instance in instances:
            record = asdict(instance) if not isinstance(instance, dict) else instance
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/fisher_cd_budget_train.jsonl"))
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2025)
    parser.add_argument(
        "--utility",
        choices=["cobb_douglas", "cobb_douglas_noisy", "linear", "leontief"],
        default="cobb_douglas",
    )
    args = parser.parse_args()
    if args.utility == "cobb_douglas":
        instances = generate_cd_instances(args.count, args.seed)
    elif args.utility == "cobb_douglas_noisy":
        instances = generate_cd_noisy_instances(args.count, args.seed)
    elif args.utility == "linear":
        instances = generate_linear_instances(args.count, args.seed)
    else:
        instances = generate_leontief_instances(args.count, args.seed)
    write_jsonl(instances, args.output)


if __name__ == "__main__":
    main()
