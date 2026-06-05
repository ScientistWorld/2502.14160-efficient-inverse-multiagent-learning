#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user

if [ "$#" -eq 0 ]; then
  python -m method.adversarial_inverse_fisher --iterations 5000 --lr-theta 0.01 --adversary-mode exact --return-iterate final
  python -m method.adversarial_inverse_fisher --instances data/fisher_linear_budget_instances.jsonl --output artifacts/fisher_linear_budgets/predictions.jsonl --iterations 5000 --lr-theta 0.01 --adversary-mode exact --return-iterate final
  python -m method.adversarial_inverse_cournot --iterations 10000 --lr-theta 0.01
  python -m method.adversarial_inverse_bertrand --iterations 250 --lr-theta 0.3
  bash scripts/evaluate.sh
else
  python -m method.adversarial_inverse_fisher "$@"
  bash scripts/evaluate.sh --experiment fisher artifacts/fisher_cd_budgets/predictions.jsonl
fi
