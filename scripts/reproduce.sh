#!/bin/bash
# Reproduce the paper's results end-to-end.
#
# This script runs inside the compute container and should call
# scripts/baseline.sh and scripts/method.sh to run baselines and
# the paper's method, each of which calls scripts/evaluate.sh.
#
# Assumes:
#   - Container is built (environment/container.sif)
#   - Data and models are downloaded (via scripts/download.sh)
#   - Working directory is /home/user
#
# This is the "gold standard" reproduction — 
# You do not need to run this, but keep this in good shape
# so other agents can easily run a full loop of reproduction and get the paper's numbers.

set -e

cd /home/user

python -m data.fisher_markets --output data/fisher_cd_budget_instances.jsonl --count 100 --seed 2025
python -m data.fisher_markets --utility linear --output data/fisher_linear_budget_instances.jsonl --count 100 --seed 2125
python -m data.fisher_markets --utility leontief --output data/fisher_leontief_budget_instances.jsonl --count 100 --seed 2225
python -m data.cournot_games --output data/cournot_instances.jsonl --count 100 --seed 3025
python -m data.bertrand_games --output data/bertrand_instances.jsonl --count 100 --seed 4025
python -m baseline.observed_expenditure
python -m method.adversarial_inverse_fisher --iterations 5000 --lr-theta 0.01 --adversary-mode exact --return-iterate final
python -m method.adversarial_inverse_fisher --instances data/fisher_linear_budget_instances.jsonl --output artifacts/fisher_linear_budgets/predictions.jsonl --iterations 5000 --lr-theta 0.01 --adversary-mode exact --return-iterate final
python -m method.adversarial_inverse_fisher --instances data/fisher_leontief_budget_instances.jsonl --output artifacts/fisher_leontief_budgets/predictions.jsonl --iterations 5000 --lr-theta 0.01 --adversary-mode exact --return-iterate final
python -m method.adversarial_inverse_cournot --iterations 10000 --lr-theta 0.01
python -m method.adversarial_inverse_bertrand --iterations 250 --lr-theta 0.3
bash scripts/evaluate.sh
