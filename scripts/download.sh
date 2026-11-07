#!/bin/bash
# Download all data and models needed for this environment.
#
# Estimated total download size: 0 GB (no external downloads)
# Estimated disk usage after extraction: < 5 MB
#
# This benchmark uses first-party synthetic market instances only; there are
# no public datasets or pretrained weights to fetch. The labeled training
# instances are regenerated below from the public generators if they are
# missing (idempotent: existing files are kept). The unlabeled held-out test
# inputs (data/*_test_inputs.jsonl) are tracked in git with the repository.
# The only dependency, numpy, is installed by environment/setup.sh.

set -e

cd /home/user

mkdir -p data/downloads

[ -f data/fisher_cd_budget_train.jsonl ] || python -m data.fisher_markets --output data/fisher_cd_budget_train.jsonl --count 100 --seed 2025
[ -f data/fisher_linear_budget_train.jsonl ] || python -m data.fisher_markets --utility linear --output data/fisher_linear_budget_train.jsonl --count 100 --seed 2125
[ -f data/fisher_cd_noisy_budget_train.jsonl ] || python -m data.fisher_markets --utility cobb_douglas_noisy --output data/fisher_cd_noisy_budget_train.jsonl --count 200 --seed 5025
[ -f data/cournot_cost_train.jsonl ] || python -m data.cournot_games --output data/cournot_cost_train.jsonl --count 100 --seed 3025

echo "Synthetic training instances ready under data/."
