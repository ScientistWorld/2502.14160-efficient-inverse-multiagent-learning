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
    leontief_best_response,
    log_leontief_utility,
    linear_best_response,
    log_linear_utility,
    read_jsonl,
)


def log_cd(allocation: np.ndarray, shares: np.ndarray) -> np.ndarray:
    return np.sum(shares * np.log(np.maximum(allocation, EPS)), axis=1)


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.maximum(exp.sum(axis=1, keepdims=True), EPS)


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


def run_cd_type_budget_algorithm_1(
    observed_allocation: np.ndarray,
    prices: np.ndarray,
    *,
    iterations: int,
    lr_theta: float,
    lr_type: float,
    seed: int,
    return_iterate: str,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Algorithm 1 for simultaneous CD type-share and budget recovery.

    The stabilizer parameters are buyer budgets and per-buyer Cobb-Douglas
    type shares.  The destabilizer has an exact allocation best-response
    oracle, so the stabilizer gradients use the envelope theorem at that
    adversarial allocation.
    """
    rng = np.random.default_rng(seed)
    num_buyers, num_goods = observed_allocation.shape
    budgets = rng.uniform(0.1, 10.0, size=num_buyers)
    logits = rng.normal(loc=0.0, scale=0.5, size=(num_buyers, num_goods))
    avg_budgets = np.zeros_like(budgets)
    avg_shares = np.zeros_like(logits)
    log_observed_allocation = np.log(np.maximum(observed_allocation, EPS))

    for _ in range(1, iterations + 1):
        shares = softmax(logits)
        y = cd_best_response(budgets, shares, prices)
        log_y = np.log(np.maximum(y, EPS))

        grad_budgets = np.sum(shares * (log_y - log_observed_allocation), axis=1)
        budgets = np.clip(budgets - lr_theta * grad_budgets, 0.001, 10.0)

        grad_shares = budgets[:, None] * (log_y - log_observed_allocation)
        centered = grad_shares - np.sum(grad_shares * shares, axis=1, keepdims=True)
        grad_logits = shares * centered
        logits = np.clip(logits - lr_type * grad_logits, -20.0, 20.0)

        avg_budgets += budgets
        avg_shares += softmax(logits)

    final_shares = softmax(logits)
    if return_iterate == "average":
        estimated_budgets = avg_budgets / float(iterations)
        estimated_shares = avg_shares / float(iterations)
        estimated_shares = estimated_shares / np.maximum(estimated_shares.sum(axis=1, keepdims=True), EPS)
    else:
        estimated_budgets = budgets
        estimated_shares = final_shares
    exploitability = fisher_regret(
        "cobb_douglas",
        estimated_budgets,
        estimated_shares,
        prices,
        observed_allocation,
    )
    return estimated_budgets, estimated_shares, exploitability


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


def run_leontief_algorithm_1(
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
    budgets = rng.uniform(0.1, 10.0, size=types.shape[0])
    y = np.maximum(observed_allocation * rng.lognormal(mean=0.0, sigma=0.2, size=observed_allocation.shape), EPS)
    avg_budgets = np.zeros_like(budgets)
    log_u_observed = log_leontief_utility(observed_allocation, types)
    for _ in range(1, iterations + 1):
        if adversary_mode == "exact":
            y = leontief_best_response(budgets, types, prices)
        else:
            grad_y = -prices[None, :] * np.ones_like(y)
            bottleneck_goods = np.argmin(y / np.maximum(types, EPS), axis=1)
            for buyer, good in enumerate(bottleneck_goods):
                grad_y[buyer, good] += budgets[buyer] / np.maximum(y[buyer, good], EPS)
            y = np.clip(y + lr_y * grad_y, EPS, 1_000.0)
        grad_budgets = log_leontief_utility(y, types) - log_u_observed
        budgets = np.clip(budgets - lr_theta * grad_budgets, 0.001, 10.0)
        avg_budgets += budgets

    averaged = avg_budgets / float(iterations)
    estimated = averaged if return_iterate == "average" else budgets
    return estimated, fisher_regret("leontief", estimated, types, prices, observed_allocation)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, default=Path("data/fisher_cd_budget_instances.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/fisher_cd_budgets/predictions.jsonl"))
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--lr-theta", type=float, default=0.01)
    parser.add_argument("--lr-type", type=float, default=0.05)
    parser.add_argument("--lr-y", type=float, default=0.01)
    parser.add_argument("--adversary-mode", choices=["exact", "gda"], default="exact")
    parser.add_argument("--return-iterate", choices=["final", "average"], default="final")
    parser.add_argument("--recover-types", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for instance in read_jsonl(args.instances):
        types = np.asarray(instance["types"], dtype=float)
        observed_allocation = np.asarray(instance["allocation"], dtype=float)
        prices = np.asarray(instance["prices"], dtype=float)
        estimated_types = None
        if args.recover_types:
            if instance["utility"] != "cobb_douglas":
                raise ValueError("--recover-types is currently implemented for Cobb-Douglas Fisher markets")
            estimated, estimated_types, exploitability = run_cd_type_budget_algorithm_1(
                observed_allocation,
                prices,
                iterations=args.iterations,
                lr_theta=args.lr_theta,
                lr_type=args.lr_type,
                seed=args.seed + int(instance["instance_id"]),
                return_iterate=args.return_iterate,
            )
        elif instance["utility"] == "linear":
            estimated, exploitability = run_linear_algorithm_1(
                types,
                observed_allocation,
                prices,
                iterations=args.iterations,
                lr_theta=args.lr_theta,
                seed=args.seed + int(instance["instance_id"]),
                return_iterate=args.return_iterate,
            )
        elif instance["utility"] == "leontief":
            estimated, exploitability = run_leontief_algorithm_1(
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
        row = {
            "instance_id": instance["instance_id"],
            "method": "adversarial_inverse_planning",
            "utility": instance["utility"],
            "estimated_budgets": estimated.tolist(),
            "diagnostic_exploitability": exploitability,
        }
        if estimated_types is not None:
            row["estimated_types"] = estimated_types.tolist()
        rows.append(row)

    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
