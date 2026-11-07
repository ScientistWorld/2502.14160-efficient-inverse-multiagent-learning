"""Simple baseline for Fisher budget recovery: observed expenditure.

Each buyer's budget is estimated as the value of the bundle it was observed
buying, ``p dot x_i``.  When a market is observed through several noisy
allocation samples, the samples are first averaged entrywise and the same
identity is applied to the averaged allocation.  This is not the paper's
method; it is the naive estimator a method should beat on noisy
observations.  It writes predictions in the evaluator's interface under
``artifacts/<experiment>/observed_expenditure/predictions.jsonl``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.fisher_markets import read_jsonl


def estimate(instance: dict) -> np.ndarray:
    prices = np.asarray(instance["prices"], dtype=float)
    if "allocation_samples" in instance:
        allocation = np.mean(np.asarray(instance["allocation_samples"], dtype=float), axis=0)
    else:
        allocation = np.asarray(instance["allocation"], dtype=float)
    return allocation @ prices


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--method-name", default="observed_expenditure")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        for path in args.instances:
            for instance in read_jsonl(path):
                handle.write(
                    json.dumps(
                        {
                            "instance_id": instance["instance_id"],
                            "method": args.method_name,
                            "utility": instance["utility"],
                            "estimated_budgets": estimate(instance).tolist(),
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )


if __name__ == "__main__":
    main()
