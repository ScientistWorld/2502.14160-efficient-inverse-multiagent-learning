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
# Estimated disk usage after extraction: 0 GB
#
# No external downloads are required. The synthetic benchmark instances are
# first-party, small, and tracked directly under data/.

set -e

cd /home/user

mkdir -p data/downloads

for required_file in \
  data/fisher_cd_budget_instances.jsonl \
  data/fisher_linear_budget_instances.jsonl \
  data/fisher_leontief_budget_instances.jsonl \
  data/cournot_instances.jsonl \
  data/bertrand_instances.jsonl
do
  test -f "$required_file"
done

echo "No downloads required."
