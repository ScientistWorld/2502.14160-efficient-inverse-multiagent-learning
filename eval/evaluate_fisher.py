"""Method-agnostic evaluator for Fisher market budget-recovery outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.fisher_markets import fisher_regret, read_jsonl, relative_l2


def read_predictions(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def summarize(rows: list[dict], instances: dict[int, dict], *, recover_types: bool = False) -> dict:
    if not rows:
        raise ValueError("No prediction rows found")
    evaluated = []
    for row in rows:
        instance = instances[int(row["instance_id"])]
        estimated = np.asarray(row["estimated_budgets"], dtype=float)
        true_budgets = np.asarray(instance["budgets"], dtype=float)
        true_types = np.asarray(instance["types"], dtype=float)
        eval_types = np.asarray(row["estimated_types"], dtype=float) if recover_types else true_types
        prices = np.asarray(instance["prices"], dtype=float)
        allocation = np.asarray(instance["allocation"], dtype=float)
        if recover_types:
            estimated_params = np.concatenate([estimated.ravel(), eval_types.ravel()])
            true_params = np.concatenate([true_budgets.ravel(), true_types.ravel()])
            rel = relative_l2(estimated_params, true_params)
        else:
            rel = relative_l2(estimated, true_budgets)
        evaluated.append(
            {
                "relative_l2": rel,
                "recovered": rel <= 0.1,
                "exploitability": fisher_regret(instance["utility"], estimated, eval_types, prices, allocation),
            }
        )
    n = len(rows)
    return {
        "parameter_recovery_rate": sum(1.0 for row in evaluated if row["recovered"]) / n,
        "average_exploitability": sum(float(row["exploitability"]) for row in evaluated) / n,
        "mean_relative_l2": sum(float(row["relative_l2"]) for row in evaluated) / n,
        "p90_relative_l2": float(np.percentile([row["relative_l2"] for row in evaluated], 90)),
        "max_exploitability": max(float(row["exploitability"]) for row in evaluated),
        "num_instances": n,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions",
        type=Path,
        nargs="+",
        default=[Path("artifacts/fisher_cd_budgets/predictions.jsonl")],
    )
    parser.add_argument("--instances", type=Path, default=Path("data/fisher_cd_budget_instances.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("scoring/scores.json"))
    parser.add_argument("--experiment-name", default="fisher_cd_budget_recovery")
    parser.add_argument("--recover-types", action="store_true")
    args = parser.parse_args()

    instances = {int(row["instance_id"]): row for row in read_jsonl(args.instances)}
    results = {}
    for prediction_path in args.predictions:
        rows = read_predictions(prediction_path)
        method_name = rows[0].get("method", prediction_path.parent.name)
        results[method_name] = summarize(rows, instances, recover_types=args.recover_types)

    scores = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else {"experiments": {}}
    scores.setdefault("experiments", {})[args.experiment_name] = {"results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
