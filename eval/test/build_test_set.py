"""Build the canonical held-out test instances (run once; the output is committed).

The seeds below exist only in ``eval/test/``.  The canonical files written to
``eval/test/instances/`` keep the ground truth; the visible copies written to
``data/*_test_inputs.jsonl`` contain only what a method may observe.  Test
instance ids start at ``TEST_ID_OFFSET`` so they never collide with the
visible training ids.

Usage (from the workspace root): ``python -m eval.test.build_test_set``.
Existing canonical files are never overwritten unless ``--force`` is given.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

from data.cournot_games import generate_cournot_instances
from data.fisher_markets import generate_cd_instances, generate_cd_noisy_instances, generate_linear_instances


HERE = Path(__file__).resolve().parent
INSTANCE_DIR = HERE / "instances"
TEST_ID_OFFSET = 100000

# name -> (generator, count, private seed, fields hidden from the method)
BUILDS = {
    "fisher_cd_budget": (generate_cd_instances, 100, 91_573_204_117, ("budgets",)),
    "fisher_linear_budget": (generate_linear_instances, 100, 66_204_981_353, ("budgets",)),
    "fisher_cd_noisy_budget": (generate_cd_noisy_instances, 200, 48_830_117_629, ("budgets", "allocation")),
    "cournot_cost": (generate_cournot_instances, 100, 27_419_665_081, ("marginal_cost",)),
}


def _records(generator, count: int, seed: int) -> list[dict]:
    # The two-good linear-market solver can reject a rare degenerate draw;
    # fall forward to the next private seed in that case.
    last_error: Exception | None = None
    for attempt in range(50):
        try:
            instances = generator(count, seed + attempt)
        except RuntimeError as exc:
            last_error = exc
            continue
        return [asdict(item) if is_dataclass(item) else dict(item) for item in instances]
    raise RuntimeError(f"could not generate instances: {last_error}")


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--inputs-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    for name, (generator, count, seed, hidden_fields) in BUILDS.items():
        canonical_path = INSTANCE_DIR / f"{name}_test.jsonl"
        inputs_path = args.inputs_dir / f"{name}_test_inputs.jsonl"
        if canonical_path.exists() and not args.force:
            print(f"keep existing {canonical_path}")
            continue
        rows = _records(generator, count, seed)
        for index, row in enumerate(rows):
            row["instance_id"] = TEST_ID_OFFSET + index
        visible = [{key: value for key, value in row.items() if key not in hidden_fields} for row in rows]
        _write(canonical_path, rows)
        _write(inputs_path, visible)
        print(f"wrote {canonical_path} and {inputs_path} ({len(rows)} instances)")


if __name__ == "__main__":
    main()
