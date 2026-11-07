# Design Notes

> **Superseded (hardening iteration, 2026-11-07):** the scored roster, data layout and evaluators changed; see `HARDENING.md`. The notes below describe the earlier gym.

Checked the train/test split for copy-paste mistakes, method detachment, train/test cross-imports, hardcoded method defaults, missing score stubs, shell syntax, and `reference.json` schema. The split evaluators score pre-generated prediction artifacts rather than re-running the method, so future method changes remain visible through their output files.

Changes made:
- Added `fisher_leontief_budget_recovery` to both `eval/train/` and `eval/test/` so the split harness covers every nonzero-weight experiment listed in `scoring/reference.json`.
- Changed the `fisher` experiment alias in both split evaluators to enumerate all Fisher utility-family recovery tasks instead of only Cobb-Douglas when no explicit experiment is selected.
- Added tail-risk metrics: `p90_relative_l2` for Fisher tasks, `p90_relative_error` for Cournot/Bertrand, and `max_exploitability` for all tasks. These make it harder to game the visible train slice by optimizing only threshold recovery rate or average error while leaving a hard subset unstable.
- Added `slice: train` / `slice: test` markers to emitted train/test score entries.
- Added required metric descriptions in `scoring/reference.json` and registered the new tail-risk metrics with nonzero constraint coefficients.

Runtime concerns for the next iteration:
- `scripts/run.sh` and the original `scripts/evaluate.sh` are outside this design pass and currently do not generate or score Leontief outputs on a fresh run, even though `reference.json` gives Leontief nonzero weight and existing artifacts include `artifacts/fisher_leontief_budgets/predictions.jsonl`. The runner iteration should align the main reproduction path with the split harness.
- Existing paper-result entries in `reference.json` were not modified to add values for the new tail-risk metrics. This preserves the paper-reported block, but comparison displays may show those metrics only for newly evaluated methods.
- The split is still parity-based over fixed synthetic instances. That is calibrated and cheap, but a future design could further improve shortcut resistance by adding a stratified split over market conditioning or cost/demand regimes if runtime budget allows.

Static checks run:
- `python -m json.tool scoring/reference.json`
- `bash -n scripts/evaluate_train.sh`
- `bash -n scripts/evaluate_test.sh`
- `python validate.py --reference-only`

No `scoring/scores_train.json` or `scoring/scores_test.json` files were present at handoff.
