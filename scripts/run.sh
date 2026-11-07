#!/bin/bash
# Hardening job: build the hidden test split, reproduce the reference, run the
# better/weaker variants, baselines and shortcuts through scripts/evaluate_test.sh,
# and regenerate the shipped scores from the reference alone.

set -euo pipefail

cd /home/user

python -m redteam.hardening.runner
