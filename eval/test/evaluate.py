"""Held-out test scorer for inverse-equilibrium parameter recovery.

Everything on the scoring side of the comparison is fixed by this directory:
the experiment roster, the canonical held-out instances (observations and
ground truth, in ``instances/``), the recovery threshold, the metric code and
the caps used for failed runs.  The only thing read from outside is the raw
prediction rows a method leaves under ``artifacts/``; no number, flag or
verdict written by a method is trusted, and nothing is imported from
``data/`` or ``method/``.

Every method found on disk is scored on every experiment.  A method whose
predictions for an experiment are missing, malformed, non-finite, outside
the parameter domain, duplicated, or that do not cover every held-out
instance exactly once is scored as *failed* on that experiment: recovery 0
and every error/exploitability metric at its cap, which is no better than
the worst value any valid prediction can receive.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
INSTANCE_DIR = HERE / "instances"
SLICE = "test"
EPS = 1e-9
RECOVERY_THRESHOLD = 0.1
RELATIVE_ERROR_CAP = 1.0
EXPLOITABILITY_CAP = 100.0


@dataclass(frozen=True)
class Spec:
    name: str
    kind: str
    artifact_dir: str
    instance_file: str
    expected_count: int
    error_metric: str
    p90_metric: str


EXPERIMENTS: tuple[Spec, ...] = (
    Spec(
        "fisher_cd_budget_recovery",
        "fisher",
        "artifacts/fisher_cd_budgets",
        "fisher_cd_budget_test.jsonl",
        100,
        "mean_relative_l2",
        "p90_relative_l2",
    ),
    Spec(
        "fisher_linear_budget_recovery",
        "fisher",
        "artifacts/fisher_linear_budgets",
        "fisher_linear_budget_test.jsonl",
        100,
        "mean_relative_l2",
        "p90_relative_l2",
    ),
    Spec(
        "fisher_cd_noisy_budget_recovery",
        "fisher",
        "artifacts/fisher_cd_noisy_budgets",
        "fisher_cd_noisy_budget_test.jsonl",
        200,
        "mean_relative_l2",
        "p90_relative_l2",
    ),
    Spec(
        "cournot_cost_recovery",
        "cournot",
        "artifacts/cournot_costs",
        "cournot_cost_test.jsonl",
        100,
        "mean_relative_error",
        "p90_relative_error",
    ),
)


class InvalidPredictions(Exception):
    """Raised when a method's predictions for an experiment cannot be scored."""


# --------------------------------------------------------------------------
# Game-side metric code (self-contained copy; deliberately not imported).
# --------------------------------------------------------------------------


def _log_cd(allocation: np.ndarray, shares: np.ndarray) -> np.ndarray:
    return np.sum(shares * np.log(np.maximum(allocation, EPS)), axis=1)


def cd_regret(budgets: np.ndarray, types: np.ndarray, prices: np.ndarray, allocation: np.ndarray) -> float:
    """Cumulative buyer regret of ``allocation`` at ``prices`` in the Eisenberg-Gale game."""
    shares = types / np.maximum(types.sum(axis=1, keepdims=True), EPS)
    best = budgets[:, None] * shares / np.maximum(prices[None, :], EPS)
    value_gap = budgets * (_log_cd(best, shares) - _log_cd(allocation, shares))
    price_gap = np.sum(prices * (allocation.sum(axis=0) - best.sum(axis=0)))
    return float(np.sum(value_gap) + price_gap)


def linear_regret(budgets: np.ndarray, types: np.ndarray, prices: np.ndarray, allocation: np.ndarray) -> float:
    bang_per_buck = types / np.maximum(prices[None, :], EPS)
    chosen = np.argmax(bang_per_buck, axis=1)
    best = np.zeros_like(types, dtype=float)
    for buyer, good in enumerate(chosen):
        best[buyer, good] = budgets[buyer] / max(float(prices[good]), EPS)

    def log_linear(alloc: np.ndarray) -> np.ndarray:
        return np.log(np.maximum(np.sum(types * alloc, axis=1), EPS))

    value_gap = budgets * (log_linear(best) - log_linear(allocation))
    price_gap = np.sum(prices * (allocation.sum(axis=0) - best.sum(axis=0)))
    return float(max(np.sum(value_gap) + price_gap, 0.0))


def fisher_regret(utility: str, budgets, types, prices, allocation) -> float:
    if utility == "cobb_douglas":
        return cd_regret(budgets, types, prices, allocation)
    if utility == "linear":
        return linear_regret(budgets, types, prices, allocation)
    raise ValueError(f"Unsupported utility in canonical instances: {utility}")


def cournot_best_response(opponent_total: float, intercept: float, slope: float, cost: float) -> float:
    return float(max((cost - intercept - slope * opponent_total) / (2.0 * slope), 0.0))


def cournot_exploitability(cost: float, intercept: float, slope: float, quantities: np.ndarray) -> float:
    total_quantity = float(np.sum(quantities))
    total = 0.0
    for observed_q in quantities:
        opponent_total = total_quantity - float(observed_q)
        deviation = cournot_best_response(opponent_total, intercept, slope, cost)
        observed_profit = float(observed_q) * (intercept + slope * total_quantity - cost)
        deviation_profit = deviation * (intercept + slope * (deviation + opponent_total) - cost)
        total += deviation_profit - observed_profit
    return float(max(total, 0.0))


def relative_l2(estimated: np.ndarray, true: np.ndarray) -> float:
    return float(np.linalg.norm((estimated - true) / np.maximum(np.abs(true), EPS)))


def relative_abs(estimated: float, true: float) -> float:
    return float(abs(estimated - true) / max(abs(true), EPS))


def bounded(value: float, cap: float) -> float:
    """Clip a per-instance error/exploitability into [0, cap]; non-finite -> cap."""
    if not math.isfinite(value):
        return cap
    return float(min(max(value, 0.0), cap))


# --------------------------------------------------------------------------
# Prediction loading and validation.
# --------------------------------------------------------------------------


def _reject_constant(token: str):
    raise ValueError(f"non-standard JSON constant {token}")


def finite_number(value, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidPredictions(f"{what} must be a JSON number")
    try:
        number = float(value)
    except (OverflowError, ValueError):
        raise InvalidPredictions(f"{what} is not representable as a float") from None
    if not math.isfinite(number):
        raise InvalidPredictions(f"{what} is not finite")
    return number


def budget_vector(value, length: int, instance_id: int) -> np.ndarray:
    if not isinstance(value, list) or len(value) != length:
        raise InvalidPredictions(f"instance {instance_id}: estimated_budgets must be a list of {length} numbers")
    vector = np.asarray([finite_number(v, f"instance {instance_id}: budget") for v in value], dtype=float)
    if np.any(vector <= 0.0):
        raise InvalidPredictions(f"instance {instance_id}: budgets must be strictly positive")
    return vector


def load_prediction_file(path: Path, fallback_name: str) -> tuple[str, list[dict], str | None]:
    """Return ``(method_name, rows, error)`` for one predictions.jsonl file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return fallback_name, [], f"unreadable prediction file: {exc}"
    rows: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line, parse_constant=_reject_constant)
        except (ValueError, RecursionError) as exc:
            return fallback_name, [], f"line {lineno}: invalid JSON ({exc})"
        if not isinstance(row, dict):
            return fallback_name, [], f"line {lineno}: each row must be a JSON object"
        rows.append(row)
    if not rows:
        return fallback_name, [], "prediction file has no rows"
    if any(row.get("method") is not None and not isinstance(row.get("method"), str) for row in rows):
        return fallback_name, [], "invalid 'method' field"
    names = {row.get("method") for row in rows}
    if len(names) != 1:
        return fallback_name, [], "rows disagree on the 'method' field"
    name = names.pop()
    if name is None:
        name = fallback_name
    if not isinstance(name, str) or not name.strip() or name.startswith("_"):
        return fallback_name, [], "invalid 'method' field"
    return name, rows, None


def discover_prediction_files(root: Path, spec: Spec) -> list[tuple[Path, str]]:
    base = root / spec.artifact_dir
    found: list[tuple[Path, str]] = []
    direct = base / "predictions.jsonl"
    if direct.is_file():
        found.append((direct, base.name))
    if base.is_dir():
        for path in sorted(base.glob("*/predictions.jsonl")):
            if path.is_file():
                found.append((path, path.parent.name))
    return found


def index_rows(rows: list[dict], instance_ids: list[int]) -> dict[int, dict]:
    by_id: dict[int, dict] = {}
    for row in rows:
        instance_id = row.get("instance_id")
        if isinstance(instance_id, bool) or not isinstance(instance_id, int):
            raise InvalidPredictions("every row needs an integer instance_id")
        if instance_id in by_id:
            raise InvalidPredictions(f"duplicate predictions for instance {instance_id}")
        by_id[instance_id] = row
    missing = [instance_id for instance_id in instance_ids if instance_id not in by_id]
    if missing:
        raise InvalidPredictions(
            f"missing predictions for {len(missing)} of {len(instance_ids)} held-out instances (e.g. {missing[0]})"
        )
    return by_id


# --------------------------------------------------------------------------
# Scoring.
# --------------------------------------------------------------------------


def summarize(spec: Spec, recovered: list[bool], errors: list[float], exploitabilities: list[float]) -> dict:
    n = len(errors)
    return {
        "parameter_recovery_rate": float(sum(1.0 for flag in recovered if flag) / n),
        "average_exploitability": float(sum(exploitabilities) / n),
        spec.error_metric: float(sum(errors) / n),
        spec.p90_metric: float(np.quantile(np.asarray(errors, dtype=float), 0.9)),
        "max_exploitability": float(max(exploitabilities)),
        "num_instances": n,
    }


def failed_metrics(spec: Spec) -> dict:
    return {
        "parameter_recovery_rate": 0.0,
        "average_exploitability": EXPLOITABILITY_CAP,
        spec.error_metric: RELATIVE_ERROR_CAP,
        spec.p90_metric: RELATIVE_ERROR_CAP,
        "max_exploitability": EXPLOITABILITY_CAP,
        "num_instances": 0,
    }


def score_fisher(spec: Spec, instances: list[dict], by_id: dict[int, dict]) -> dict:
    parsed = []
    for instance in instances:
        instance_id = int(instance["instance_id"])
        true_budgets = np.asarray(instance["budgets"], dtype=float)
        estimate = budget_vector(by_id[instance_id].get("estimated_budgets"), true_budgets.size, instance_id)
        parsed.append((instance, true_budgets, estimate))
    recovered, errors, exploitabilities = [], [], []
    with np.errstate(all="ignore"):
        for instance, true_budgets, estimate in parsed:
            rel = relative_l2(estimate, true_budgets)
            recovered.append(bool(rel <= RECOVERY_THRESHOLD))
            errors.append(bounded(rel, RELATIVE_ERROR_CAP))
            regret = fisher_regret(
                instance["utility"],
                estimate,
                np.asarray(instance["types"], dtype=float),
                np.asarray(instance["prices"], dtype=float),
                np.asarray(instance["allocation"], dtype=float),
            )
            exploitabilities.append(bounded(regret, EXPLOITABILITY_CAP))
    return summarize(spec, recovered, errors, exploitabilities)


def score_cournot(spec: Spec, instances: list[dict], by_id: dict[int, dict]) -> dict:
    parsed = []
    for instance in instances:
        instance_id = int(instance["instance_id"])
        estimate = finite_number(
            by_id[instance_id].get("estimated_marginal_cost"), f"instance {instance_id}: estimated_marginal_cost"
        )
        if estimate < 0.0:
            raise InvalidPredictions(f"instance {instance_id}: marginal cost must be non-negative")
        parsed.append((instance, estimate))
    recovered, errors, exploitabilities = [], [], []
    with np.errstate(all="ignore"):
        for instance, estimate in parsed:
            rel = relative_abs(estimate, float(instance["marginal_cost"]))
            recovered.append(bool(rel <= RECOVERY_THRESHOLD))
            errors.append(bounded(rel, RELATIVE_ERROR_CAP))
            regret = cournot_exploitability(
                estimate,
                float(instance["intercept"]),
                float(instance["slope"]),
                np.asarray(instance["quantities"], dtype=float),
            )
            exploitabilities.append(bounded(regret, EXPLOITABILITY_CAP))
    return summarize(spec, recovered, errors, exploitabilities)


def score(spec: Spec, instances: list[dict], rows: list[dict]) -> dict:
    by_id = index_rows(rows, [int(instance["instance_id"]) for instance in instances])
    if spec.kind == "fisher":
        return score_fisher(spec, instances, by_id)
    if spec.kind == "cournot":
        return score_cournot(spec, instances, by_id)
    raise ValueError(f"Unknown experiment kind {spec.kind}")


def load_canonical(spec: Spec) -> list[dict]:
    path = INSTANCE_DIR / spec.instance_file
    with path.open("r", encoding="utf-8") as handle:
        instances = [json.loads(line) for line in handle if line.strip()]
    if len(instances) != spec.expected_count:
        raise SystemExit(f"{path}: expected {spec.expected_count} canonical instances, found {len(instances)}")
    return instances


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=Path("scoring/scores_test.json"))
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    canonical = {spec.name: load_canonical(spec) for spec in EXPERIMENTS}

    files: dict[str, dict[str, list[tuple[Path, list[dict], str | None]]]] = {}
    for spec in EXPERIMENTS:
        per_method: dict[str, list[tuple[Path, list[dict], str | None]]] = {}
        for path, fallback in discover_prediction_files(args.root, spec):
            name, rows, error = load_prediction_file(path, fallback)
            per_method.setdefault(name, []).append((path, rows, error))
        files[spec.name] = per_method

    methods = sorted({name for per_method in files.values() for name in per_method})
    if not methods:
        print("No prediction artifacts found under artifacts/; nothing to score.", file=sys.stderr)
        sys.exit(1)

    scores: dict = {"experiments": {}}
    for spec in EXPERIMENTS:
        results: dict[str, dict] = {}
        failures: dict[str, str] = {}
        for method in methods:
            entries = files[spec.name].get(method, [])
            try:
                if not entries:
                    raise InvalidPredictions(f"no predictions under {spec.artifact_dir}/")
                if len(entries) > 1:
                    raise InvalidPredictions("several prediction files claim this method name")
                _, rows, error = entries[0]
                if error:
                    raise InvalidPredictions(error)
                results[method] = score(spec, canonical[spec.name], rows)
            except InvalidPredictions as exc:
                results[method] = failed_metrics(spec)
                failures[method] = str(exc)
            except Exception as exc:  # any other malformed input still fails only this method
                results[method] = failed_metrics(spec)
                failures[method] = f"unscorable predictions ({type(exc).__name__}: {exc})"
        block: dict = {"slice": SLICE, "results": results}
        if failures:
            block["failures"] = failures
        scores["experiments"][spec.name] = block

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scores, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    for spec in EXPERIMENTS:
        block = scores["experiments"][spec.name]
        for method, metrics in block["results"].items():
            status = "FAILED: " + block["failures"][method] if method in block.get("failures", {}) else "ok"
            print(
                f"[{SLICE}] {spec.name} {method}: recovery={metrics['parameter_recovery_rate']:.4f} "
                f"{spec.error_metric}={metrics[spec.error_metric]:.6g} "
                f"avg_exploitability={metrics['average_exploitability']:.6g} ({status})"
            )


if __name__ == "__main__":
    main()
