#!/bin/bash
# Reproduce the reference results end-to-end (CPU only, a few minutes).
#
# 1. Regenerate the visible labeled training instances if missing (public seeds).
#    The held-out test inputs in data/*_test_inputs.jsonl are tracked in git;
#    their ground truth lives only with the hidden test evaluator.
# 2. Run the paper's method on train + test inputs (scripts/method.sh).
# 3. Score the visible train split and the held-out test split.

set -e

cd /home/user

[ -f data/fisher_cd_budget_train.jsonl ] || python -m data.fisher_markets --output data/fisher_cd_budget_train.jsonl --count 100 --seed 2025
[ -f data/fisher_linear_budget_train.jsonl ] || python -m data.fisher_markets --utility linear --output data/fisher_linear_budget_train.jsonl --count 100 --seed 2125
[ -f data/fisher_cd_noisy_budget_train.jsonl ] || python -m data.fisher_markets --utility cobb_douglas_noisy --output data/fisher_cd_noisy_budget_train.jsonl --count 200 --seed 5025
[ -f data/cournot_cost_train.jsonl ] || python -m data.cournot_games --output data/cournot_cost_train.jsonl --count 100 --seed 3025

bash scripts/method.sh
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
