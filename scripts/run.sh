#!/bin/bash
# Example job script submitted via the end-of-turn YAML block.
#
# This runs inside the compute container with:
#   - Your workspace mounted at /home/user
#   - GPU(s) available
#   - No internet access
#
# Make sure all data, code, and dependencies are already in the
# workspace or baked into the container before submitting.

set -e

cd /home/user

python -m data.fisher_markets --output data/fisher_cd_budget_instances.jsonl --count 100 --seed 2025
python -m data.fisher_markets --utility linear --output data/fisher_linear_budget_instances.jsonl --count 100 --seed 2125
python -m data.cournot_games --output data/cournot_instances.jsonl --count 100 --seed 3025
python -m data.bertrand_games --output data/bertrand_instances.jsonl --count 100 --seed 4025
python -m baseline.observed_expenditure
python -m method.adversarial_inverse_fisher --iterations 5000 --lr-theta 0.01 --adversary-mode exact --return-iterate final
python -m method.adversarial_inverse_fisher --instances data/fisher_linear_budget_instances.jsonl --output artifacts/fisher_linear_budgets/predictions.jsonl --iterations 5000 --lr-theta 0.01 --adversary-mode exact --return-iterate final
python -m method.adversarial_inverse_cournot --iterations 10000 --lr-theta 0.01
python -m method.adversarial_inverse_bertrand --iterations 250 --lr-theta 0.3
bash scripts/evaluate.sh
