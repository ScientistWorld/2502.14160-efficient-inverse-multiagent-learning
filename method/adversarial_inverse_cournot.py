"""Adversarial inverse planning for duopoly Cournot competition.

The unknown game parameter is marginal cost c.  Given observed equilibrium
quantities q*, Algorithm 1's inverse-regret objective is

    min_c max_y sum_i profit_i(y_i, q*_-i; c) - profit_i(q*; c).

For the linear inverse demand used in the paper, each firm's adversarial
quantity best response has a closed form, giving an exact adversary oracle for
the same min-max objective.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.cournot_games import best_response, cournot_exploitability, read_jsonl, relative_abs


def recover_cost(
    intercept: float,
    slope: float,
    quantities: np.ndarray,
    *,
    iterations: int,
    lr_theta: float,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    cost = float(rng.uniform(2.0, 20.0))
    for _ in range(iterations):
        grad = 0.0
        for i, observed_q in enumerate(quantities):
            opponent_total = float(np.sum(quantities) - observed_q)
            y = best_response(opponent_total, intercept, slope, cost)
            grad += observed_q - y
        cost = float(np.clip(cost - lr_theta * grad, 2.0, 20.0))
    return cost, cournot_exploitability(cost, intercept, slope, quantities)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, default=Path("data/cournot_instances.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/cournot_costs/predictions.jsonl"))
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--lr-theta", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for instance in read_jsonl(args.instances):
            quantities = np.asarray(instance["quantities"], dtype=float)
            estimated, exploitability = recover_cost(
                float(instance["intercept"]),
                float(instance["slope"]),
                quantities,
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
