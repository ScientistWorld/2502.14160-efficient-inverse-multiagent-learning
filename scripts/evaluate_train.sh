#!/bin/bash
# Score every method on disk on the visible train split -> scoring/scores_train.json.
# Same interface, validation rules and metrics as the held-out test split.
# Takes no arguments.

set -e

cd /home/user

mkdir -p scoring
rm -f scoring/scores_train.json
python -m eval.train.evaluate --output scoring/scores_train.json
