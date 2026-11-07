#!/bin/bash
# Run the accepted static inverse-equilibrium reproduction suite.

set -e

cd /home/user

bash scripts/reproduce.sh
python validate.py --compare
