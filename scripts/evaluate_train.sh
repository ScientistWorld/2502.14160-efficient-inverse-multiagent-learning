#!/bin/bash
# Evaluate the visible train slice for all available prediction artifacts.
# Mirrors scripts/evaluate.sh, but writes scoring/scores_train.json.

set -e

cd /home/user

mkdir -p scoring

if [ "$#" -eq 0 ]; then
  rm -f scoring/scores_train.json
  python -m eval.train.evaluate --output scoring/scores_train.json
elif [ "$1" = "--experiment" ]; then
  experiment="$2"
  shift 2
  python -m eval.train.evaluate --output scoring/scores_train.json --experiment "$experiment" "$@"
else
  python -m eval.train.evaluate --output scoring/scores_train.json --experiment fisher "$@"
fi
