#!/bin/bash
# Score the visible train and held-out test evaluation slices.

set -e

cd /home/user

bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
