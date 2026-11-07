# Evaluation

## Data

| Experiment | Visible labeled training instances | Held-out test inputs (no labels) | Artifact directory |
|---|---|---|---|
| `fisher_cd_budget_recovery` | `data/fisher_cd_budget_train.jsonl` (100) | `data/fisher_cd_budget_test_inputs.jsonl` (100) | `artifacts/fisher_cd_budgets/` |
| `fisher_linear_budget_recovery` | `data/fisher_linear_budget_train.jsonl` (100) | `data/fisher_linear_budget_test_inputs.jsonl` (100) | `artifacts/fisher_linear_budgets/` |
| `fisher_cd_noisy_budget_recovery` | `data/fisher_cd_noisy_budget_train.jsonl` (200) | `data/fisher_cd_noisy_budget_test_inputs.jsonl` (200) | `artifacts/fisher_cd_noisy_budgets/` |
| `cournot_cost_recovery` | `data/cournot_cost_train.jsonl` (100) | `data/cournot_cost_test_inputs.jsonl` (100) | `artifacts/cournot_costs/` |

Training rows include the ground truth (`budgets`, `marginal_cost`, and for the sampled-observation experiment the true equilibrium `allocation`). Test-input rows contain only what may be observed. Training instance IDs are `0..N-1` and test instance IDs start at `100000`. The test ground truth lives only with the hidden test scorer. Train and test instances come from the same generators and distributions.

## Prediction Format

Write one JSON object per line to `artifacts/<artifact directory>/predictions.jsonl`, or to `artifacts/<artifact directory>/<your_method>/predictions.jsonl` to keep several methods side by side. Every row needs:

- `instance_id`: the integer ID of the instance;
- `method`: a non-empty string naming your method, identical on every row and in every experiment;
- `estimated_budgets`: a list of 3 finite, strictly positive numbers (Fisher experiments); or
- `estimated_marginal_cost`: one finite, non-negative number (Cournot).

Cover every training and every test instance. Extra fields are ignored. Scores are always recomputed from these raw estimates.

## Metrics

All metrics are computed per instance and averaged over the split:

- `parameter_recovery_rate`: fraction of instances whose relative parameter error is at most 0.1. For budget vectors this is the L2 norm of the elementwise relative errors; for costs it is the absolute relative error. Higher is better.
- `mean_relative_l2` (budgets) / `mean_relative_error` (costs): mean relative parameter error, with each instance capped at 1.0. Lower is better.
- `p90_relative_l2` / `p90_relative_error`: 90th percentile of the per-instance relative error (tail accuracy). Lower is better.
- `average_exploitability`: mean total regret, under the recovered parameters, of the true equilibrium behavior. For Fisher markets this is the buyers' regret in the Eisenberg-Gale market game at the equilibrium prices; for Cournot it is the firms' total profitable unilateral deviation. Each instance is capped at 100. Lower is better.
- `max_exploitability`: worst per-instance exploitability. Lower is better.
- `num_instances`: number of scored instances (informational).

**Failure rule.** A method's run on an experiment is scored as *failed* if its predictions are missing for any instance of the split, contain duplicate IDs, are not valid JSON (including `NaN`/`Infinity`), have the wrong shape, are non-finite or fall outside the domain (non-positive budgets, negative costs). A failed run gets recovery 0 and every error and exploitability metric at its cap. A method that writes no predictions for an experiment is also scored as failed there. The roster of experiments, the instances, the recovery threshold and the caps are fixed by the evaluator.

## Ranking

Experiments are weighted 0.4 (`fisher_cd_noisy_budget_recovery`) and 0.2 each (the other three). A method's rank relative to the reference adds, over experiments, `weight * sum_metric coefficient * (method value - reference value)` with the coefficients in `scoring/reference.json`: recovery +1.0, mean error -1.0, average exploitability -0.8, p90 error -0.35, max exploitability -0.25.

## Baselines and Targets

Paper-reported results for the exact-observation settings (500 instances each): Cobb-Douglas Fisher budget recovery 100% recovery, average exploitability 0.0004; linear Fisher budget recovery 100%, 0.0018; Cournot cost recovery 95.2%, 0.0000. The paper does not report the sampled-observation setting.

Reference results on the held-out test split: 100% recovery on all three exact-observation experiments, with mean relative errors of about 1e-3 (Fisher) and 3e-6 (Cournot). On the sampled-observation experiment the reference reaches 60.5% recovery, mean relative L2 0.093 and average exploitability 0.024. The simple baseline in `baseline/observed_expenditure.py` estimates each budget as the value of the observed bundle, averaging the noisy samples first. On the sampled-observation test split it reaches 34% recovery and mean relative L2 0.127; using a single sample instead gives 3.5% and 0.373. The exact-observation experiments are nearly at their bounds; the sampled-observation experiment leaves substantial room above the reference.

## Evaluation Protocol

1. Run your method so it writes predictions for every training and test instance in the format above.
2. `bash scripts/evaluate_train.sh` writes `scoring/scores_train.json` (the visible split; `bash scripts/evaluate.sh` writes the same numbers to `scoring/scores.json`).
3. The hidden test split is scored by `bash scripts/evaluate_test.sh` with no arguments. It scores every method found under `artifacts/` on every experiment and writes `scoring/scores_test.json`.

The evaluators use only code in `eval/` and the raw prediction files; they never import `method/`.
