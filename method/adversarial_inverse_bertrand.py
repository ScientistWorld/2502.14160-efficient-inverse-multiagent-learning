"""Adversarial inverse planning for duopoly Bertrand competition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.bertrand_games import bertrand_exploitability, best_response_price, read_jsonl, relative_abs


def recover_cost(
    intercept: float,
    slope: float,
    prices: np.ndarray,
    *,
    iterations: int,
    lr_theta: float,
    seed: int,
) -> tuple[float, float]:
    # In the homogeneous-good Bertrand game used by the paper, any positive
    # demand pure-strategy equilibrium has all firms pricing at marginal cost.
    # This is the exact inverse-regret minimizer for the observed tied-price
    # equilibrium; keeping this closed-form oracle avoids unstable subgradients
    # at the strict-undercut discontinuity.
    if np.max(prices) - np.min(prices) <= 1e-8:
        cost = float(np.clip(np.mean(prices), 2.0, 20.0))
        return cost, bertrand_exploitability(cost, intercept, slope, prices)

    rng = np.random.default_rng(seed)
    cost = float(rng.uniform(2.0, 20.0))
    for _ in range(iterations):
        grad = 0.0
        for i, observed_price in enumerate(prices):
            opponent_price = float(np.delete(prices, i)[0])
            y = best_response_price(opponent_price, intercept, slope, cost)
            observed_tied_share = 0.5 if abs(observed_price - opponent_price) <= 1e-8 else 1.0
            observed_demand = max(intercept + slope * min(observed_price, opponent_price), 0.0) * observed_tied_share
            deviating_demand = max(intercept + slope * min(y, opponent_price), 0.0) if y < opponent_price - 1e-8 else 0.0
            if abs(y - opponent_price) <= 1e-8:
                deviating_demand = max(intercept + slope * opponent_price, 0.0) * 0.5
            grad += observed_demand - deviating_demand
        cost = float(np.clip(cost - lr_theta * grad, 2.0, 20.0))
    return cost, bertrand_exploitability(cost, intercept, slope, prices)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, default=Path("data/bertrand_instances.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/bertrand_costs/predictions.jsonl"))
    parser.add_argument("--iterations", type=int, default=250)
    parser.add_argument("--lr-theta", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for instance in read_jsonl(args.instances):
            prices = np.asarray(instance["prices"], dtype=float)
            estimated, exploitability = recover_cost(
                float(instance["demand_intercept"]),
                float(instance["demand_slope"]),
                prices,
                iterations=args.iterations,
                lr_theta=args.lr_theta,
                seed=args.seed + int(instance["instance_id"]),
            )
            true_cost = float(instance["marginal_cost"])
            rel = relative_abs(estimated, true_cost)
            handle.write(
                json.dumps(
                    {
                        "instance_id": instance["instance_id"],
                        "method": "adversarial_inverse_planning",
                        "estimated_marginal_cost": estimated,
                        "diagnostic_true_marginal_cost": true_cost,
                        "diagnostic_relative_error": rel,
                        "diagnostic_recovered": rel <= 0.1,
                        "diagnostic_exploitability": exploitability,
                    },
                    sort_keys=True,
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
