"""Hardening-iteration runner (one CPU job).

1. Builds the hidden canonical test set (eval/test/instances) and the visible
   inputs/training files that do not exist yet.
2. Produces predictions for the reference method (three seeds), a stronger
   and a weaker training variant, simple baselines, a headroom demonstration
   and every shortcut, each into its own folder under tmp/hardening/.
3. Installs each case's predictions (and any data tampering it performs) in
   the workspace, runs ``bash scripts/evaluate_train.sh`` and
   ``bash scripts/evaluate_test.sh`` with no arguments as fresh processes,
   archives the score files, and restores the workspace byte for byte.
4. Computes rank changes against the reference with the weights and
   coefficients of scoring/reference.json and writes summary.json/summary.md.
5. Leaves the reference (seed 7) predictions installed and regenerates the
   shipped scoring/scores*.json from them alone.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HARD = ROOT / "redteam" / "hardening"
CASES_OUT = HARD / "cases"
WORK = ROOT / "tmp" / "hardening"
BACKUP = ROOT / "tmp" / "hardening_backup"
PY = sys.executable
REF_METHOD = "adversarial_inverse_planning"

# experiment -> (data stem, artifact dir, kind)
EXPERIMENTS = {
    "fisher_cd_budget_recovery": ("fisher_cd_budget", "fisher_cd_budgets", "fisher"),
    "fisher_linear_budget_recovery": ("fisher_linear_budget", "fisher_linear_budgets", "fisher"),
    "fisher_cd_noisy_budget_recovery": ("fisher_cd_noisy_budget", "fisher_cd_noisy_budgets", "fisher"),
    "cournot_cost_recovery": ("cournot_cost", "cournot_costs", "cournot"),
}


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def run(cmd: list[str], env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    log("$ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    if proc.stdout.strip():
        print(proc.stdout.strip()[-4000:], flush=True)
    if proc.stderr.strip():
        print(proc.stderr.strip()[-4000:], flush=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}")
    return proc


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def visible_rows(stem: str) -> list[dict]:
    return read_jsonl(ROOT / "data" / f"{stem}_train.jsonl") + read_jsonl(ROOT / "data" / f"{stem}_test_inputs.jsonl")


def clean_artifacts() -> None:
    target = ROOT / "artifacts"
    target.mkdir(exist_ok=True)
    for child in target.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


# ---------------------------------------------------------------------------
# Step 1: data
# ---------------------------------------------------------------------------


def build_data() -> None:
    run([PY, "-m", "eval.test.build_test_set"])
    if not (ROOT / "data" / "fisher_cd_noisy_budget_train.jsonl").exists():
        run([PY, "-m", "data.fisher_markets", "--utility", "cobb_douglas_noisy", "--output",
             "data/fisher_cd_noisy_budget_train.jsonl", "--count", "200", "--seed", "5025"])


# ---------------------------------------------------------------------------
# Step 2: predictions
# ---------------------------------------------------------------------------


def method_case(name: str, fisher_iterations: int, cournot_iterations: int, fisher_seed: int, cournot_seed: int) -> None:
    out = WORK / name / "artifacts"
    if out.exists():
        shutil.rmtree(out)
    env = dict(os.environ)
    env.update(
        ARTIFACTS=str(out),
        FISHER_ITERATIONS=str(fisher_iterations),
        COURNOT_ITERATIONS=str(cournot_iterations),
        FISHER_SEED=str(fisher_seed),
        COURNOT_SEED=str(cournot_seed),
    )
    start = time.time()
    run(["bash", "scripts/method.sh"], env=env)
    (WORK / name / "runtime_seconds.txt").write_text(f"{time.time() - start:.1f}\n")


def case_artifacts(name: str) -> Path:
    return WORK / name / "artifacts"


def write_case(name: str, experiment: str, rows: list[dict], subdir: str | None = None) -> None:
    artifact_dir = EXPERIMENTS[experiment][1]
    base = case_artifacts(name) / artifact_dir
    if subdir:
        base = base / subdir
    write_jsonl(base / "predictions.jsonl", rows)


def write_raw_case(name: str, experiment: str, lines: list[str]) -> None:
    path = case_artifacts(name) / EXPERIMENTS[experiment][1] / "predictions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")


def reference_rows(experiment: str, case: str = "reference_seed7") -> list[dict]:
    return read_jsonl(case_artifacts(case) / EXPERIMENTS[experiment][1] / "predictions.jsonl")


def shares_of(types: np.ndarray) -> np.ndarray:
    return types / types.sum(axis=1, keepdims=True)


def fisher_identity(row: dict, pooling: str) -> list[float]:
    prices = np.asarray(row["prices"], dtype=float)
    if "allocation_samples" not in row:
        return (np.asarray(row["allocation"], dtype=float) @ prices).tolist()
    samples = np.asarray(row["allocation_samples"], dtype=float)
    if pooling == "arithmetic":
        return (samples.mean(axis=0) @ prices).tolist()
    if pooling == "single":
        return (samples[0] @ prices).tolist()
    shares = shares_of(np.asarray(row["types"], dtype=float))
    log_b = np.sum(shares * (np.log(samples).mean(axis=0) + np.log(prices)[None, :] - np.log(shares)), axis=1)
    return np.exp(log_b).tolist()


def cournot_identity(row: dict) -> float:
    quantities = np.asarray(row["quantities"], dtype=float)
    total = float(np.sum(quantities))
    return float(np.mean([row["intercept"] + row["slope"] * (total + q) for q in quantities]))


def clearing_constrained_budgets(row: dict) -> list[float]:
    """Headroom demo: noise-aware estimate restricted to market-clearing budgets.

    With exact posted prices and unit supplies, equilibrium budgets satisfy
    shares^T b = p.  Fit log-budgets to the per-good log-expenditure evidence
    (equal weights) on that line.
    """
    prices = np.asarray(row["prices"], dtype=float)
    shares = shares_of(np.asarray(row["types"], dtype=float))
    samples = np.asarray(row["allocation_samples"], dtype=float)
    evidence = np.log(samples).mean(axis=0) + np.log(prices)[None, :] - np.log(shares)
    target = evidence.mean(axis=1)
    a = shares.T
    b0, *_ = np.linalg.lstsq(a, prices, rcond=None)
    direction = np.cross(a[0], a[1])
    direction = direction / np.linalg.norm(direction)
    lo, hi = -math.inf, math.inf
    for b_i, v_i in zip(b0, direction):
        if v_i > 1e-12:
            lo = max(lo, -b_i / v_i)
        elif v_i < -1e-12:
            hi = min(hi, -b_i / v_i)
        elif b_i <= 0:
            return np.exp(target).tolist()
    if not (math.isfinite(lo) and math.isfinite(hi) and lo < hi):
        return np.exp(target).tolist()

    def objective(t: float) -> float:
        b = b0 + t * direction
        return float(np.sum((np.log(np.maximum(b, 1e-300)) - target) ** 2))

    grid = np.linspace(lo, hi, 4001)[1:-1]
    values = [objective(float(t)) for t in grid]
    k = int(np.argmin(values))
    left, right = float(grid[max(k - 1, 0)]), float(grid[min(k + 1, len(grid) - 1)])
    for _ in range(100):
        m1 = left + (right - left) / 3.0
        m2 = right - (right - left) / 3.0
        if objective(m1) <= objective(m2):
            right = m2
        else:
            left = m1
    t = 0.5 * (left + right)
    return (b0 + t * direction).tolist()


def build_derived_cases() -> dict[str, dict]:
    """Construct baseline, headroom-demo and shortcut predictions. Returns per-case metadata."""
    meta: dict[str, dict] = {}

    # Honest closed-form alternatives and baselines -------------------------------------
    for name, pooling, method in (
        ("closed_form_arithmetic_pooling", "arithmetic", "closed_form_arithmetic_pooling"),
        ("closed_form_log_pooling", "log", "closed_form_log_pooling"),
        ("closed_form_single_sample", "single", "closed_form_single_sample"),
    ):
        for experiment, (stem, _, kind) in EXPERIMENTS.items():
            rows = []
            for row in visible_rows(stem):
                if kind == "fisher":
                    rows.append({"instance_id": row["instance_id"], "method": method,
                                 "estimated_budgets": fisher_identity(row, pooling)})
                else:
                    rows.append({"instance_id": row["instance_id"], "method": method,
                                 "estimated_marginal_cost": cournot_identity(row)})
            write_case(name, experiment, rows)
        meta[name] = {"method": method, "kind": "honest_alternative"}

    # Shipped simple baseline (Fisher only, as scripts/baseline.sh writes it) --------------
    for experiment, (stem, artifact_dir, kind) in EXPERIMENTS.items():
        if kind != "fisher":
            continue
        out = case_artifacts("shipped_baseline_observed_expenditure") / artifact_dir / "observed_expenditure" / "predictions.jsonl"
        run([PY, "-m", "baseline.observed_expenditure", "--instances", f"data/{stem}_train.jsonl",
             f"data/{stem}_test_inputs.jsonl", "--output", str(out)])
    meta["shipped_baseline_observed_expenditure"] = {"method": "observed_expenditure", "kind": "baseline"}

    # Headroom demonstration: reference everywhere except a clearing-constrained estimate on noisy
    try:
        build_clearing_demo()
        meta["better_clearing_constrained_demo"] = {"method": "clearing_constrained_demo", "kind": "better_variant"}
    except Exception as exc:  # keep the rest of the audit running
        log(f"clearing demo failed: {type(exc).__name__}: {exc}")

    _build_shortcuts(meta)
    return meta


def build_clearing_demo() -> None:
    for experiment, (stem, _, kind) in EXPERIMENTS.items():
        rows = []
        if experiment == "fisher_cd_noisy_budget_recovery":
            for row in visible_rows(stem):
                rows.append({"instance_id": row["instance_id"], "method": "clearing_constrained_demo",
                             "estimated_budgets": clearing_constrained_budgets(row)})
        else:
            for row in reference_rows(experiment):
                rows.append({**row, "method": "clearing_constrained_demo"})
        write_case("better_clearing_constrained_demo", experiment, rows)


def _build_shortcuts(meta: dict[str, dict]) -> None:
    # Shortcuts ------------------------------------------------------------------------------
    def constant_rows(experiment: str, budget_value, cost_value, method: str, extra: dict | None = None) -> list[dict]:
        stem, _, kind = EXPERIMENTS[experiment]
        rows = []
        for row in visible_rows(stem):
            out = {"instance_id": row["instance_id"], "method": method}
            if kind == "fisher":
                out["estimated_budgets"] = budget_value
            else:
                out["estimated_marginal_cost"] = cost_value
            if extra:
                out.update(extra)
            rows.append(out)
        return rows

    # label copy: copy every label the visible data exposes
    for experiment, (stem, _, kind) in EXPERIMENTS.items():
        rows = []
        for row in visible_rows(stem):
            if kind == "fisher" and "budgets" in row:
                rows.append({"instance_id": row["instance_id"], "method": "label_copy", "estimated_budgets": row["budgets"]})
            elif kind == "cournot" and "marginal_cost" in row:
                rows.append({"instance_id": row["instance_id"], "method": "label_copy",
                             "estimated_marginal_cost": row["marginal_cost"]})
        write_case("shortcut_label_copy", experiment, rows)
    meta["shortcut_label_copy"] = {"method": "label_copy", "kind": "shortcut"}

    # cherry pick: repeat the single lowest-regret reference row in place of every row
    for experiment in EXPERIMENTS:
        rows = reference_rows(experiment)
        test_rows = [row for row in rows if row["instance_id"] >= 100000]
        train_rows = [row for row in rows if row["instance_id"] < 100000]
        picked = []
        for group in (train_rows, test_rows):
            best = min(group, key=lambda row: float(row.get("diagnostic_exploitability", 0.0)))
            picked.extend([dict(best) for _ in group])
        write_case("shortcut_cherry_pick", experiment, picked)
    meta["shortcut_cherry_pick"] = {"method": REF_METHOD, "kind": "shortcut"}

    # rewrite labels: reference predictions, and the visible data files' label fields are overwritten
    for experiment in EXPERIMENTS:
        write_case("shortcut_rewrite_labels", experiment, reference_rows(experiment))
    meta["shortcut_rewrite_labels"] = {"method": REF_METHOD, "kind": "shortcut", "data_mutation": "rewrite_labels"}

    # replace fixed data: constant predictions + visible data replaced by equilibria of those constants
    for experiment in EXPERIMENTS:
        write_case("shortcut_replace_fixed_data", experiment, constant_rows(experiment, [5.0, 5.0, 5.0], 11.0, "replace_fixed_data"))
    meta["shortcut_replace_fixed_data"] = {"method": "replace_fixed_data", "kind": "shortcut", "data_mutation": "replace_fixed_data"}

    # forged scores/flags
    for experiment in EXPERIMENTS:
        write_case("shortcut_forged_scores_flags", experiment, constant_rows(
            experiment, [5.0, 5.0, 5.0], 11.0, "forged_scores_flags",
            extra={"parameter_recovery_rate": 1.0, "recovered": True, "diagnostic_exploitability": -1e9,
                   "exploitability": 0.0, "relative_error": 0.0}))
    meta["shortcut_forged_scores_flags"] = {"method": "forged_scores_flags", "kind": "shortcut", "prewrite_scores": True}

    for name, budget_value, cost_value in (
        ("shortcut_constant", [5.0, 5.0, 5.0], 11.0),
        ("shortcut_zero", [0.0, 0.0, 0.0], 0.0),
        ("shortcut_negative", [-1.0, -1.0, -1.0], -1.0),
        ("shortcut_empty", [], []),
        ("shortcut_null", None, None),
    ):
        for experiment in EXPERIMENTS:
            write_case(name, experiment, constant_rows(experiment, budget_value, cost_value, name.replace("shortcut_", "")))
        meta[name] = {"method": name.replace("shortcut_", ""), "kind": "shortcut"}

    for name, token in (("shortcut_nan", "NaN"), ("shortcut_inf", "Infinity")):
        for experiment, (stem, _, kind) in EXPERIMENTS.items():
            lines = []
            for row in visible_rows(stem):
                value = f"[{token}, {token}, {token}]" if kind == "fisher" else token
                key = "estimated_budgets" if kind == "fisher" else "estimated_marginal_cost"
                lines.append(f'{{"instance_id": {row["instance_id"]}, "method": "{name.replace("shortcut_", "")}", "{key}": {value}}}')
            write_raw_case(name, experiment, lines)
        meta[name] = {"method": name.replace("shortcut_", ""), "kind": "shortcut"}

    # New probes against the hardened evaluator
    for experiment in EXPERIMENTS:
        if experiment != "fisher_cd_noisy_budget_recovery":
            write_case("shortcut_drop_hard_experiment", experiment, reference_rows(experiment))
    meta["shortcut_drop_hard_experiment"] = {"method": REF_METHOD, "kind": "shortcut"}

    for experiment in EXPERIMENTS:
        rows = reference_rows(experiment)
        if experiment == "fisher_cd_noisy_budget_recovery":
            lines = []
            poisoned = False
            for row in rows:
                if not poisoned and row["instance_id"] >= 100000:
                    row = dict(row)
                    row["estimated_budgets"] = "__NAN__"
                    poisoned = True
                lines.append(json.dumps(row, sort_keys=True).replace('"__NAN__"', "[NaN, 1.0, 1.0]"))
            write_raw_case("shortcut_one_nan_row", experiment, lines)
        else:
            write_case("shortcut_one_nan_row", experiment, rows)
    meta["shortcut_one_nan_row"] = {"method": REF_METHOD, "kind": "shortcut"}

    for experiment in EXPERIMENTS:
        rows = reference_rows(experiment)
        test_ids = [row["instance_id"] for row in rows if row["instance_id"] >= 100000]
        dropped = set(test_ids[: len(test_ids) // 2])
        write_case("shortcut_subset_coverage", experiment, [row for row in rows if row["instance_id"] not in dropped])
    meta["shortcut_subset_coverage"] = {"method": REF_METHOD, "kind": "shortcut"}


# ---------------------------------------------------------------------------
# Step 3: evaluation through the hidden test
# ---------------------------------------------------------------------------


def snapshot() -> None:
    if BACKUP.exists():
        shutil.rmtree(BACKUP)
    BACKUP.mkdir(parents=True)
    for name in ("artifacts", "data", "scoring"):
        shutil.copytree(ROOT / name, BACKUP / name, ignore=shutil.ignore_patterns("__pycache__"))


def restore() -> None:
    for name in ("artifacts", "data", "scoring"):
        target = ROOT / name
        shutil.rmtree(target)
        shutil.copytree(BACKUP / name, target)


def mutate_data(kind: str, case: str) -> None:
    sys.path.insert(0, str(ROOT))
    from data.cournot_games import equilibrium_quantities
    from data.fisher_markets import cobb_douglas_equilibrium, linear_equilibrium

    for experiment, (stem, _, exp_kind) in EXPERIMENTS.items():
        predictions = {row["instance_id"]: row for row in reference_rows(experiment)}
        for suffix in ("_train.jsonl", "_test_inputs.jsonl"):
            path = ROOT / "data" / f"{stem}{suffix}"
            rows = read_jsonl(path)
            for row in rows:
                if kind == "rewrite_labels":
                    prediction = predictions[row["instance_id"]]
                    if exp_kind == "fisher":
                        row["budgets"] = prediction["estimated_budgets"]
                    else:
                        row["marginal_cost"] = prediction["estimated_marginal_cost"]
                elif kind == "replace_fixed_data":
                    if exp_kind == "fisher":
                        budgets = np.asarray([5.0, 5.0, 5.0])
                        types = np.asarray(row["types"], dtype=float)
                        solver = linear_equilibrium if row["utility"] == "linear" else cobb_douglas_equilibrium
                        prices, allocation = solver(types, budgets)
                        row["budgets"] = budgets.tolist()
                        row["prices"] = prices.tolist()
                        row["allocation"] = allocation.tolist()
                        if "allocation_samples" in row:
                            row["allocation_samples"] = [allocation.tolist()] * len(row["allocation_samples"])
                    else:
                        row["marginal_cost"] = 11.0
                        row["quantities"] = equilibrium_quantities(2, float(row["intercept"]), float(row["slope"]), 11.0).tolist()
            write_jsonl(path, rows)


def evaluate_case(case: str, meta: dict) -> dict:
    out_dir = CASES_OUT / case
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    status: dict = {"case": case, **meta}
    try:
        clean_artifacts()
        source = case_artifacts(case)
        for child in source.iterdir():
            shutil.copytree(child, ROOT / "artifacts" / child.name)
        if meta.get("data_mutation"):
            mutate_data(meta["data_mutation"], case)
        if meta.get("prewrite_scores"):
            forged = {"experiments": {exp: {"results": {meta["method"]: {"parameter_recovery_rate": 1.0}}} for exp in EXPERIMENTS}}
            (ROOT / "scoring" / "scores_test.json").write_text(json.dumps(forged))
        for split in ("train", "test"):
            proc = subprocess.run(["bash", f"scripts/evaluate_{split}.sh"], cwd=ROOT, capture_output=True, text=True)
            (out_dir / f"{split}.log").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr)
            status[f"{split}_returncode"] = proc.returncode
            produced = ROOT / "scoring" / f"scores_{split}.json"
            if produced.exists():
                shutil.copy2(produced, out_dir / f"scores_{split}.json")
    finally:
        restore()
    (out_dir / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    return status


# ---------------------------------------------------------------------------
# Step 4: ranking
# ---------------------------------------------------------------------------


def rank_delta(candidate: dict, anchor: dict, method: str, reference: dict) -> float | None:
    total = 0.0
    for experiment, spec in reference["experiments"].items():
        cand_block = candidate.get("experiments", {}).get(experiment, {}).get("results", {})
        anchor_block = anchor["experiments"][experiment]["results"][REF_METHOD]
        if method not in cand_block:
            return None
        cand = cand_block[method]
        for metric, definition in spec["metrics"].items():
            coefficient = float(definition["coefficient"])
            if coefficient == 0.0:
                continue
            total += float(spec["weight"]) * coefficient * (float(cand[metric]) - float(anchor_block[metric]))
    return total


def summarize(metas: dict[str, dict]) -> None:
    reference = json.loads((ROOT / "scoring" / "reference.json").read_text())
    anchors = {split: json.loads((CASES_OUT / "reference_seed7" / f"scores_{split}.json").read_text()) for split in ("train", "test")}
    rows = []
    for case, meta in metas.items():
        entry = {"case": case, **meta}
        for split in ("train", "test"):
            path = CASES_OUT / case / f"scores_{split}.json"
            if not path.exists():
                entry[f"{split}_rank_delta"] = None
                continue
            scores = json.loads(path.read_text())
            entry[f"{split}_rank_delta"] = rank_delta(scores, anchors[split], meta["method"], reference)
            per_exp = {}
            for experiment in reference["experiments"]:
                block = scores["experiments"].get(experiment, {})
                metrics = block.get("results", {}).get(meta["method"])
                per_exp[experiment] = {
                    "metrics": metrics,
                    "failure": block.get("failures", {}).get(meta["method"]),
                }
            entry[f"{split}_experiments"] = per_exp
        rows.append(entry)
    seeds = [r["test_rank_delta"] for r in rows if r["case"].startswith("reference_seed") and r["test_rank_delta"] is not None]
    summary = {
        "reference_weights": {k: v["weight"] for k, v in reference["experiments"].items()},
        "seed_spread_test": (max(seeds) - min(seeds)) if seeds else None,
        "cases": rows,
    }
    (HARD / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    lines = ["| case | kind | train rank delta | test rank delta | noisy recovery (test) | noisy mean rel L2 (test) | failures (test) |",
             "|---|---|---:|---:|---:|---:|---|"]
    for r in rows:
        noisy = (r.get("test_experiments") or {}).get("fisher_cd_noisy_budget_recovery", {})
        metrics = noisy.get("metrics") or {}
        failures = [exp for exp, data in (r.get("test_experiments") or {}).items() if data.get("failure")]

        def fmt(value):
            return "n/a" if value is None else f"{value:+.6g}"

        lines.append(
            f"| {r['case']} | {r['kind']} | {fmt(r.get('train_rank_delta'))} | {fmt(r.get('test_rank_delta'))} | "
            f"{metrics.get('parameter_recovery_rate', float('nan')):.3f} | {metrics.get('mean_relative_l2', float('nan')):.4f} | "
            f"{', '.join(failures) if failures else '-'} |"
        )
    lines.append("")
    lines.append(f"Seed spread of the reference (max-min test rank delta over seeds 7/8/9): {summary['seed_spread_test']}")
    (HARD / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


# ---------------------------------------------------------------------------


def main() -> None:
    os.chdir(ROOT)
    WORK.mkdir(parents=True, exist_ok=True)
    CASES_OUT.mkdir(parents=True, exist_ok=True)
    build_data()

    metas: dict[str, dict] = {}
    for name, fi, ci, fs, cs, kind in (
        ("reference_seed7", 5000, 10000, 7, 17, "reference"),
        ("reference_seed8", 5000, 10000, 8, 18, "reference"),
        ("reference_seed9", 5000, 10000, 9, 19, "reference"),
        ("weaker_training", 1, 1, 7, 17, "weaker_variant"),
        ("stronger_training", 20000, 40000, 7, 17, "stronger_variant"),
    ):
        method_case(name, fi, ci, fs, cs)
        metas[name] = {"method": REF_METHOD, "kind": kind, "fisher_iterations": fi, "cournot_iterations": ci,
                       "fisher_seed": fs, "cournot_seed": cs}
    metas.update(build_derived_cases())

    clean_artifacts()
    snapshot()
    for case, meta in metas.items():
        log(f"evaluating case {case}")
        status = evaluate_case(case, meta)
        log(f"  -> train rc={status.get('train_returncode')} test rc={status.get('test_returncode')}")

    try:
        summarize(metas)
    except Exception as exc:
        log(f"summary failed: {type(exc).__name__}: {exc}")

    # Ship the reference alone.
    clean_artifacts()
    for child in case_artifacts("reference_seed7").iterdir():
        shutil.copytree(child, ROOT / "artifacts" / child.name)
    run(["bash", "scripts/evaluate.sh"])
    run(["bash", "scripts/evaluate_train.sh"])
    run(["bash", "scripts/evaluate_test.sh"])
    run([PY, "validate.py", "--compare"], check=False)
    run([PY, "validate.py", "--post-design"], check=False)
    log("hardening run complete")


if __name__ == "__main__":
    main()
