#!/bin/bash
# Run the paper method on the static inverse-equilibrium reproduction suite,
# including the pending Cobb-Douglas type-and-budget setting.

set -e

cd /home/user

bash scripts/reproduce.sh
python validate.py --compare
