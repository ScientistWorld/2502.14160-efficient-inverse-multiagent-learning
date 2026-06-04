#!/bin/bash
# Download all data and models needed for this environment.
#
# Run on a node with internet access BEFORE building the container
# or submitting compute jobs.
#
# This script should be idempotent — safe to run multiple times.
# It should skip files that already exist.
#
# Update the storage estimate below as you add downloads.
#
# Estimated total download size: 0 GB
# Estimated disk usage after extraction: <1 MB
#
# No external downloads are required. This script deterministically regenerates
# the small synthetic benchmark file used by the reproduction.

set -e

cd /home/user

python -m data.fisher_markets --output data/fisher_cd_budget_instances.jsonl --count 100 --seed 2025
python -m data.fisher_markets --utility linear --output data/fisher_linear_budget_instances.jsonl --count 100 --seed 2125
python -m data.cournot_games --output data/cournot_instances.jsonl --count 100 --seed 3025
python -m data.bertrand_games --output data/bertrand_instances.jsonl --count 100 --seed 4025
