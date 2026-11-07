#!/bin/bash
# Score every method on disk on the held-out test split -> scoring/scores_test.json.
# Ground truth, roster, thresholds and metric code all live in eval/test/.
# Takes no arguments.

set -e

cd /home/user

mkdir -p scoring
rm -f scoring/scores_test.json
python -m eval.test.evaluate --output scoring/scores_test.json
