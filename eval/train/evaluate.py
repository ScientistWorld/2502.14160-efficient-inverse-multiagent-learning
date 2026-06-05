"""Visible train-slice scorer for inverse-equilibrium prediction artifacts.

This evaluator deliberately scores only pre-generated method outputs.  It
splits each experiment's fixed evaluation instances by ``instance_id`` parity:
even IDs are visible train examples, odd IDs are held out for ``eval/test``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from data.bertrand_games import bertrand_exploitability
from data.cournot_games import cournot_exploitability
from data.fisher_markets import fisher_regret, relative_l2


SLICE = "train"
PARITY = 0


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    kind: str
    artifact_dir: Path
    instances: Path
    recover_types: bool = False


EXPERIMENTS: tuple[ExperimentSpec, ...] = (
    ExperimentSpec(
        "fisher_cd_budget_recovery",
        "fisher",
        Path("artifacts/fisher_cd_budgets"),
        Path("data/fisher_cd_budget_instances.jsonl"),
    ),
    ExperimentSpec(
        "fisher_linear_budget_recovery",
        "fisher",
        Path("artifacts/fisher_linear_budgets"),
        Path("data/fisher_linear_budget_instances.jsonl"),
    ),
    ExperimentSpec(
        "cournot_cost_recovery",
        "cournot",
        Path("artifacts/cournot_costs"),
        Path("data/cournot_instances.jsonl"),
    ),
    ExperimentSpec(
        "bertrand_cost_recovery",
        "bertrand",
        Path("artifacts/bertrand_costs"),
        Path("data/bertrand_instances.jsonl"),
    ),
)


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_scores(path: Path, scores: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def method_name_for(rows: list[dict], prediction_path: Path) -> str:
    return str(rows[0].get("method") or prediction_path.parent.name)


def slice_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if int(row["instance_id"]) % 2 == PARITY]


def discover_prediction_paths(spec: ExperimentSpec) -> list[Path]:
    candidates: list[Path] = []
    direct = spec.artifact_dir / "predictions.jsonl"
    if direct.is_file():
        candidates.append(direct)
    if spec.artifact_dir.is_dir():
        candidates.extend(sorted(spec.artifact_dir.glob("*/predictions.jsonl")))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def summarize_fisher(rows: list[dict], instances: dict[int, dict], *, recover_types: bool = False) -> dict:
    if not rows:
        raise ValueError(f"No {SLICE} prediction rows found")
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
    n = len(evaluated)
    return {
        "parameter_recovery_rate": sum(1.0 for row in evaluated if row["recovered"]) / n,
        "average_exploitability": sum(float(row["exploitability"]) for row in evaluated) / n,
        "mean_relative_l2": sum(float(row["relative_l2"]) for row in evaluated) / n,
        "p90_relative_l2": float(np.quantile([row["relative_l2"] for row in evaluated], 0.9)),
        "max_exploitability": max(float(row["exploitability"]) for row in evaluated),
        "num_instances": n,
    }


def relative_abs(estimated: float, true: float) -> float:
    return float(abs(estimated - true) / max(abs(true), 1e-9))


def summarize_cournot(rows: list[dict], instances: dict[int, dict]) -> dict:
    if not rows:
        raise ValueError(f"No {SLICE} prediction rows found")
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
        "p90_relative_error": float(np.quantile([row["relative_error"] for row in evaluated], 0.9)),
        "max_exploitability": max(float(row["exploitability"]) for row in evaluated),
        "num_instances": n,
    }


def summarize_bertrand(rows: list[dict], instances: dict[int, dict]) -> dict:
    if not rows:
        raise ValueError(f"No {SLICE} prediction rows found")
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
                "exploitability": bertrand_exploitability(
                    estimated,
                    float(instance["demand_intercept"]),
                    float(instance["demand_slope"]),
                    np.asarray(instance["prices"], dtype=float),
                ),
            }
        )
    n = len(evaluated)
    return {
        "parameter_recovery_rate": sum(1.0 for row in evaluated if row["recovered"]) / n,
        "average_exploitability": sum(float(row["exploitability"]) for row in evaluated) / n,
        "mean_relative_error": sum(float(row["relative_error"]) for row in evaluated) / n,
        "p90_relative_error": float(np.quantile([row["relative_error"] for row in evaluated], 0.9)),
        "max_exploitability": max(float(row["exploitability"]) for row in evaluated),
        "num_instances": n,
    }


def summarize(spec: ExperimentSpec, rows: list[dict], instances: dict[int, dict]) -> dict:
    if spec.kind == "fisher":
        return summarize_fisher(rows, instances, recover_types=spec.recover_types)
    if spec.kind == "cournot":
        return summarize_cournot(rows, instances)
    if spec.kind == "bertrand":
        return summarize_bertrand(rows, instances)
    raise ValueError(f"Unsupported experiment kind: {spec.kind}")


def evaluate_spec(spec: ExperimentSpec, prediction_paths: list[Path]) -> dict:
    instances = {int(row["instance_id"]): row for row in read_jsonl(spec.instances)}
    results: dict[str, dict] = {}
    for prediction_path in prediction_paths:
        rows = read_jsonl(prediction_path)
        if not rows:
            raise ValueError(f"No prediction rows found in {prediction_path}")
        sliced = slice_rows(rows)
        method_name = method_name_for(rows, prediction_path)
        results[method_name] = summarize(spec, sliced, instances)
    return results


def experiment_specs_for(alias: str) -> list[ExperimentSpec]:
    if alias == "fisher":
        return [spec for spec in EXPERIMENTS if spec.kind == "fisher"]
    if alias == "cournot":
        return [spec for spec in EXPERIMENTS if spec.kind == "cournot"]
    if alias == "bertrand":
        return [spec for spec in EXPERIMENTS if spec.kind == "bertrand"]
    for spec in EXPERIMENTS:
        if spec.name == alias:
            return [spec]
    raise ValueError(f"Unknown experiment: {alias}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("scoring/scores_train.json"))
    parser.add_argument("--experiment", choices=["fisher", "cournot", "bertrand"] + [s.name for s in EXPERIMENTS])
    parser.add_argument("predictions", nargs="*", type=Path)
    args = parser.parse_args()

    selected_specs = experiment_specs_for(args.experiment) if args.experiment else list(EXPERIMENTS)
    scores = {"experiments": {}}
    for spec in selected_specs:
        prediction_paths = args.predictions if args.predictions else discover_prediction_paths(spec)
        if not prediction_paths:
            continue
        scores["experiments"][spec.name] = {"slice": SLICE, "results": evaluate_spec(spec, prediction_paths)}

    if not scores["experiments"]:
        raise SystemExit("No prediction artifacts found to score")
    write_scores(args.output, scores)


if __name__ == "__main__":
    main()
