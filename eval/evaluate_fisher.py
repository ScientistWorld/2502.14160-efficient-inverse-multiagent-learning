"""Method-agnostic evaluator for Fisher market budget-recovery outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_predictions(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def summarize(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("No prediction rows found")
    n = len(rows)
    return {
        "parameter_recovery_rate": sum(1.0 for row in rows if row["recovered"]) / n,
        "average_exploitability": sum(float(row["exploitability"]) for row in rows) / n,
        "mean_relative_l2": sum(float(row["relative_l2"]) for row in rows) / n,
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
    parser.add_argument("--output", type=Path, default=Path("scoring/scores.json"))
    args = parser.parse_args()

    results = {}
    for prediction_path in args.predictions:
        rows = read_predictions(prediction_path)
        method_name = rows[0].get("method", prediction_path.parent.name)
        results[method_name] = summarize(rows)

    scores = {
        "experiments": {
            "fisher_cd_budget_recovery": {
                "results": results,
            }
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
