#!/bin/bash
# Run the simple observed-expenditure baseline on the Fisher experiments.
#
# Writes artifacts/<experiment>/observed_expenditure/predictions.jsonl so the
# evaluators pick it up as method "observed_expenditure". It makes no Cournot
# predictions, so it is scored as failed on cournot_cost_recovery.
#
# Usage:
#   bash scripts/baseline.sh

set -e

cd /home/user

for experiment in fisher_cd_budget:fisher_cd_budgets fisher_linear_budget:fisher_linear_budgets fisher_cd_noisy_budget:fisher_cd_noisy_budgets; do
  name="${experiment%%:*}"
  out_dir="${experiment##*:}"
  python -m baseline.observed_expenditure \
    --instances "data/${name}_train.jsonl" "data/${name}_test_inputs.jsonl" \
    --output "artifacts/${out_dir}/observed_expenditure/predictions.jsonl"
done

bash scripts/evaluate.sh
