"""Method-agnostic evaluator for Cournot marginal-cost recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.cournot_games import cournot_exploitability, read_jsonl, relative_abs


def read_predictions(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def summarize(rows: list[dict], instances: dict[int, dict]) -> dict:
    evaluated = []
    for row in rows:
        instance = instances[int(row["instance_id"])]
        estimated = float(row["estimated_marginal_cost"])
        true_cost = float(instance["marginal_cost"])
        rel = relative_abs(estimated, true_cost)
        evaluated.append(
            {
                "relative_error": rel,
                "recovered": rel <= 0.1,
                "exploitability": cournot_exploitability(
                    estimated,
                    float(instance["intercept"]),
                    float(instance["slope"]),
                    np.asarray(instance["quantities"], dtype=float),
                ),
            }
        )
    n = len(evaluated)
    return {
        "parameter_recovery_rate": sum(1.0 for row in evaluated if row["recovered"]) / n,
        "average_exploitability": sum(float(row["exploitability"]) for row in evaluated) / n,
        "mean_relative_error": sum(float(row["relative_error"]) for row in evaluated) / n,
        "p90_relative_error": float(np.percentile([row["relative_error"] for row in evaluated], 90)),
        "max_exploitability": max(float(row["exploitability"]) for row in evaluated),
        "num_instances": n,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, default=Path("artifacts/cournot_costs/predictions.jsonl"))
    parser.add_argument("--instances", type=Path, default=Path("data/cournot_instances.jsonl"))
    parser.add_argument("--scores", type=Path, default=Path("scoring/scores.json"))
    args = parser.parse_args()

    scores = json.loads(args.scores.read_text(encoding="utf-8")) if args.scores.exists() else {"experiments": {}}
    rows = read_predictions(args.predictions)
    instances = {int(row["instance_id"]): row for row in read_jsonl(args.instances)}
    method_name = rows[0].get("method", args.predictions.parent.name)
    scores.setdefault("experiments", {})["cournot_cost_recovery"] = {
        "results": {
            method_name: summarize(rows, instances),
        }
    }
    args.scores.parent.mkdir(parents=True, exist_ok=True)
    args.scores.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
