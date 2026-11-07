#!/bin/bash
# Run the paper's proposed method (adversarial inverse planning / learning,
# Algorithm 1 with exact adversary oracles) on every scored experiment.
#
# Predictions cover both the labeled training instances (data/*_train.jsonl)
# and the unlabeled held-out test inputs (data/*_test_inputs.jsonl); the
# evaluators score each split separately.
#
# Optional environment overrides (defaults reproduce the reference):
#   ARTIFACTS, FISHER_ITERATIONS, COURNOT_ITERATIONS, FISHER_SEED, COURNOT_SEED
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user

ARTIFACTS="${ARTIFACTS:-artifacts}"
FISHER_ITERATIONS="${FISHER_ITERATIONS:-5000}"
COURNOT_ITERATIONS="${COURNOT_ITERATIONS:-10000}"
FISHER_SEED="${FISHER_SEED:-7}"
COURNOT_SEED="${COURNOT_SEED:-17}"

for experiment in fisher_cd_budget:fisher_cd_budgets fisher_linear_budget:fisher_linear_budgets fisher_cd_noisy_budget:fisher_cd_noisy_budgets; do
  name="${experiment%%:*}"
  out_dir="${experiment##*:}"
  python -m method.adversarial_inverse_fisher \
    --instances "data/${name}_train.jsonl" "data/${name}_test_inputs.jsonl" \
    --output "${ARTIFACTS}/${out_dir}/predictions.jsonl" \
    --iterations "${FISHER_ITERATIONS}" --lr-theta 0.01 --seed "${FISHER_SEED}" \
    --adversary-mode exact --return-iterate final
done

python -m method.adversarial_inverse_cournot \
  --instances data/cournot_cost_train.jsonl data/cournot_cost_test_inputs.jsonl \
  --output "${ARTIFACTS}/cournot_costs/predictions.jsonl" \
  --iterations "${COURNOT_ITERATIONS}" --lr-theta 0.01 --seed "${COURNOT_SEED}"

if [ "${ARTIFACTS}" = "artifacts" ]; then
  bash scripts/evaluate.sh
fi
