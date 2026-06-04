"""Simple diagnostic baseline for Fisher budget recovery.

This baseline estimates each buyer's budget as observed expenditure p* dot X*_i.
It is not the paper's method; it validates the benchmark and provides a strong
oracle-style reference for the CD budget-identification task.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.fisher_markets import cd_regret, read_jsonl, relative_l2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, default=Path("data/fisher_cd_budget_instances.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/baseline_observed_expenditure/predictions.jsonl"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        for instance in read_jsonl(args.instances):
            types = np.asarray(instance["types"], dtype=float)
            allocation = np.asarray(instance["allocation"], dtype=float)
            prices = np.asarray(instance["prices"], dtype=float)
            true_budgets = np.asarray(instance["budgets"], dtype=float)
            estimated = allocation @ prices
            handle.write(
                json.dumps(
                    {
                        "instance_id": instance["instance_id"],
                        "method": "observed_expenditure",
                        "utility": instance["utility"],
                        "estimated_budgets": estimated.tolist(),
                        "true_budgets": true_budgets.tolist(),
                        "relative_l2": relative_l2(estimated, true_budgets),
                        "recovered": bool(relative_l2(estimated, true_budgets) <= 0.1),
                        "exploitability": cd_regret(estimated, types, prices, allocation),
                    },
                    sort_keys=True,
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
