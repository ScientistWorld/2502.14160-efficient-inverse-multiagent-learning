"""Recompute hardening rank deltas from archived case scores (stdlib only).

Rank delta = sum over experiments in scoring/reference.json of
weight * sum over metrics of coefficient * (candidate - reference), where the
reference is the shipped reference run (case ``reference_seed7``).  If a
case's intended method name is absent (e.g. its files were unparseable and
were attributed to directory-name fallbacks), the best rank among the
methods actually scored is reported, which is the most favourable reading
for the shortcut.

Usage: python3 redteam/hardening/rank.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARD = ROOT / "redteam" / "hardening"
CASES = HARD / "cases"
REF_METHOD = "adversarial_inverse_planning"

# Test rank change on the pre-hardening gym, copied from REDTEAM.md (None = no finite rank / not run).
BEFORE = {
    "reference_seed7": 0.0,
    "reference_seed8": 2.64076065967e-05,
    "reference_seed9": 1.98905833514e-05,
    "stronger_training": 0.000612021006375,
    "weaker_training": -10.6452278725,
    "closed_form_arithmetic_pooling": 0.000612021081855,
    "shortcut_label_copy": 0.000612021081855,
    "shortcut_cherry_pick": 0.000612014259362,
    "shortcut_rewrite_labels": 0.000605984912274,
    "shortcut_replace_fixed_data": 0.000612021081858,
    "shortcut_forged_scores_flags": -16.5808860976,
    "shortcut_constant": -16.5808860976,
    "shortcut_zero": -72.2111999085,
    "shortcut_negative": -105.770927271,
    "shortcut_empty": None,
    "shortcut_null": None,
    "shortcut_nan": None,
    "shortcut_inf": None,
}


def rank_delta(candidate: dict, anchor: dict, method: str, reference: dict) -> float | None:
    total = 0.0
    for experiment, spec in reference["experiments"].items():
        block = candidate.get("experiments", {}).get(experiment, {}).get("results", {})
        if method not in block:
            return None
        cand = block[method]
        base = anchor["experiments"][experiment]["results"][REF_METHOD]
        for metric, definition in spec["metrics"].items():
            coefficient = float(definition["coefficient"])
            if coefficient:
                total += float(spec["weight"]) * coefficient * (float(cand[metric]) - float(base[metric]))
    return total


def main() -> None:
    reference = json.loads((ROOT / "scoring" / "reference.json").read_text())
    anchors = {s: json.loads((CASES / "reference_seed7" / f"scores_{s}.json").read_text()) for s in ("train", "test")}
    rows = []
    for case_dir in sorted(p for p in CASES.iterdir() if p.is_dir()):
        status = json.loads((case_dir / "status.json").read_text())
        entry = {"case": case_dir.name, "kind": status["kind"], "method": status["method"],
                 "before_test_rank_delta": BEFORE.get(case_dir.name, "not run")}
        for split in ("train", "test"):
            path = case_dir / f"scores_{split}.json"
            if not path.exists():
                entry[f"{split}_rank_delta"] = None
                continue
            scores = json.loads(path.read_text())
            method = status["method"]
            value = rank_delta(scores, anchors[split], method, reference)
            if value is None:
                names = set()
                for block in scores["experiments"].values():
                    names |= set(block["results"])
                values = [rank_delta(scores, anchors[split], name, reference) for name in sorted(names)]
                values = [v for v in values if v is not None]
                value = max(values) if values else None
                entry[f"{split}_attributed_to"] = "best of fallback method names"
                method = None
            entry[f"{split}_rank_delta"] = value
            per_exp = {}
            for experiment in reference["experiments"]:
                block = scores["experiments"].get(experiment, {})
                per_exp[experiment] = {
                    "metrics": block.get("results", {}).get(method) if method else None,
                    "failure": block.get("failures", {}).get(method) if method else "all fallback methods failed"
                    if block.get("failures") else None,
                }
            entry[f"{split}_experiments"] = per_exp
        rows.append(entry)

    order = {"reference": 0, "stronger_variant": 1, "weaker_variant": 2, "better_variant": 3,
             "honest_alternative": 4, "baseline": 5, "shortcut": 6}
    rows.sort(key=lambda r: (order.get(r["kind"], 9), r["case"]))
    seeds = [r["test_rank_delta"] for r in rows if r["case"].startswith("reference_seed")]
    summary = {
        "reference_weights": {k: v["weight"] for k, v in reference["experiments"].items()},
        "seed_spread_test": max(seeds) - min(seeds),
        "cases": rows,
    }
    (HARD / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    def fmt(value) -> str:
        if value is None:
            return "no finite rank"
        if isinstance(value, str):
            return value
        return f"{value:+.6g}"

    def exp_cell(entry: dict, experiment: str, metric: str) -> str:
        data = (entry.get("test_experiments") or {}).get(experiment) or {}
        if data.get("failure"):
            return "failed"
        metrics = data.get("metrics") or {}
        return f"{metrics[metric]:.3f}" if metric in metrics else "n/a"

    lines = [
        "| case | kind | before: test rank | after: train rank | after: test rank | test recovery CD / linear / Cournot / noisy | noisy mean rel L2 |",
        "|---|---|---:|---:|---:|---|---:|",
    ]
    for r in rows:
        recov = " / ".join(exp_cell(r, e, "parameter_recovery_rate") for e in
                           ("fisher_cd_budget_recovery", "fisher_linear_budget_recovery", "cournot_cost_recovery",
                            "fisher_cd_noisy_budget_recovery"))
        lines.append(
            f"| {r['case']} | {r['kind']} | {fmt(r['before_test_rank_delta'])} | {fmt(r.get('train_rank_delta'))} | "
            f"{fmt(r.get('test_rank_delta'))} | {recov} | {exp_cell(r, 'fisher_cd_noisy_budget_recovery', 'mean_relative_l2')} |"
        )
    lines.append("")
    lines.append(f"Reference seed spread (max - min test rank over seeds 7/8/9): {summary['seed_spread_test']:.6g}")
    (HARD / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
