#!/bin/bash
# Evaluation script — the standard way to evaluate work in this environment.
#
# Self-contained: uses only code in eval/ and never imports method/.
# Scores every method that wrote predictions under artifacts/<experiment>/
# (either artifacts/<experiment>/predictions.jsonl or
# artifacts/<experiment>/<anything>/predictions.jsonl) on the visible,
# labeled training instances and writes scoring/scores.json.
# See briefing/evaluation.md for the prediction format.
#
# Usage:
#   bash scripts/evaluate.sh

set -e

cd /home/user

mkdir -p scoring
rm -f scoring/scores.json
python -m eval.train.evaluate --output scoring/scores.json
