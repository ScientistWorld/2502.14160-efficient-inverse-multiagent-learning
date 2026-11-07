#!/bin/bash
# Reproduce the reference end to end: training data (if missing), the paper's
# method on train + held-out test inputs, train/test scoring, and validation.
# (The hardening audit itself is `python -m redteam.hardening.runner`.)

set -euo pipefail

cd /home/user

bash scripts/reproduce.sh
python validate.py --post-design
