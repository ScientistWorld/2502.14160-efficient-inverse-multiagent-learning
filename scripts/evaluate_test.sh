#!/bin/bash
# Evaluate the held-out test slice for all methods scored on train.
# Mirrors scripts/evaluate.sh, but writes scoring/scores_test.json.

set -e

cd /home/user

mkdir -p scoring

if [ "$#" -eq 0 ]; then
  rm -f scoring/scores_test.json
  python -m eval.test.evaluate --output scoring/scores_test.json --train-scores scoring/scores_train.json
elif [ "$1" = "--experiment" ]; then
  experiment="$2"
  shift 2
  python -m eval.test.evaluate --output scoring/scores_test.json --train-scores scoring/scores_train.json --experiment "$experiment" "$@"
else
  python -m eval.test.evaluate --output scoring/scores_test.json --train-scores scoring/scores_train.json --experiment fisher "$@"
fi
