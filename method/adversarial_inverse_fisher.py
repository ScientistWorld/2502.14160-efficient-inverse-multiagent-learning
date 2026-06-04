"""Adversarial inverse multiagent planning for static Fisher markets.

This is Algorithm 1 from the paper specialized to the Eisenberg-Gale game for
static Fisher markets with observed competitive equilibrium (X*, p*) and known
utility types.  It minimizes over candidate budgets and
maximizes over adversarial allocations:

    min_b max_Y sum_i b_i [log u_i(Y_i) - log u_i(X*_i)]
              + p* dot (sum_i X*_i - sum_i Y_i).

The gradients are exact first-order oracle evaluations for this game.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.fisher_markets import (
    EPS,
    cd_best_response,
    fisher_regret,
    linear_best_response,
    log_linear_utility,
    read_jsonl,
    relative_l2,
)


def log_cd(allocation: np.ndarray, shares: np.ndarray) -> np.ndarray:
    return np.sum(shares * np.log(np.maximum(allocation, EPS)), axis=1)


def run_algorithm_1(
    types: np.ndarray,
    observed_allocation: np.ndarray,
    prices: np.ndarray,
    *,
    iterations: int,
    lr_theta: float,
    lr_y: float,
    seed: int,
    adversary_mode: str,
    return_iterate: str,
) -> tuple[np.ndarray, float]:
    rng = np.random.default_rng(seed)
    shares = types / np.maximum(types.sum(axis=1, keepdims=True), EPS)
    budgets = rng.uniform(0.1, 10.0, size=types.shape[0])
    y = np.maximum(observed_allocation * rng.lognormal(mean=0.0, sigma=0.2, size=observed_allocation.shape), EPS)
    avg_budgets = np.zeros_like(budgets)

    log_u_observed = log_cd(observed_allocation, shares)
    for _ in range(1, iterations + 1):
        if adversary_mode == "exact":
            y = cd_best_response(budgets, shares, prices)
        else:
            grad_y = budgets[:, None] * shares / np.maximum(y, EPS) - prices[None, :]
            y = np.clip(y + lr_y * grad_y, EPS, 1_000.0)

        grad_budgets = log_cd(y, shares) - log_u_observed
        budgets = np.clip(budgets - lr_theta * grad_budgets, 0.001, 10.0)
        avg_budgets += budgets

    averaged = avg_budgets / float(iterations)
    estimated = averaged if return_iterate == "average" else budgets
    return estimated, fisher_regret("cobb_douglas", estimated, types, prices, observed_allocation)


def run_linear_algorithm_1(
    types: np.ndarray,
    observed_allocation: np.ndarray,
    prices: np.ndarray,
    *,
    iterations: int,
    lr_theta: float,
    seed: int,
    return_iterate: str,
) -> tuple[np.ndarray, float]:
    rng = np.random.default_rng(seed)
    budgets = rng.uniform(0.1, 10.0, size=types.shape[0])
    avg_budgets = np.zeros_like(budgets)
    log_u_observed = log_linear_utility(observed_allocation, types)
    for _ in range(1, iterations + 1):
        y = linear_best_response(budgets, types, prices)
        grad_budgets = log_linear_utility(y, types) - log_u_observed
        budgets = np.clip(budgets - lr_theta * grad_budgets, 0.001, 10.0)
        avg_budgets += budgets

    averaged = avg_budgets / float(iterations)
    estimated = averaged if return_iterate == "average" else budgets
    return estimated, fisher_regret("linear", estimated, types, prices, observed_allocation)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, default=Path("data/fisher_cd_budget_instances.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/fisher_cd_budgets/predictions.jsonl"))
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--lr-theta", type=float, default=0.01)
    parser.add_argument("--lr-y", type=float, default=0.01)
    parser.add_argument("--adversary-mode", choices=["exact", "gda"], default="exact")
    parser.add_argument("--return-iterate", choices=["final", "average"], default="final")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for instance in read_jsonl(args.instances):
        types = np.asarray(instance["types"], dtype=float)
        observed_allocation = np.asarray(instance["allocation"], dtype=float)
        prices = np.asarray(instance["prices"], dtype=float)
        true_budgets = np.asarray(instance["budgets"], dtype=float)
        if instance["utility"] == "linear":
            estimated, exploitability = run_linear_algorithm_1(
                types,
                observed_allocation,
                prices,
                iterations=args.iterations,
                lr_theta=args.lr_theta,
                seed=args.seed + int(instance["instance_id"]),
                return_iterate=args.return_iterate,
            )
        else:
            estimated, exploitability = run_algorithm_1(
                types,
                observed_allocation,
                prices,
                iterations=args.iterations,
                lr_theta=args.lr_theta,
                lr_y=args.lr_y,
                seed=args.seed + int(instance["instance_id"]),
                adversary_mode=args.adversary_mode,
                return_iterate=args.return_iterate,
            )
        rows.append(
            {
                "instance_id": instance["instance_id"],
                "method": "adversarial_inverse_planning",
                "utility": instance["utility"],
                "estimated_budgets": estimated.tolist(),
                "diagnostic_true_budgets": true_budgets.tolist(),
                "diagnostic_relative_l2": relative_l2(estimated, true_budgets),
                "diagnostic_recovered": bool(relative_l2(estimated, true_budgets) <= 0.1),
                "diagnostic_exploitability": exploitability,
            }
        )

    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
