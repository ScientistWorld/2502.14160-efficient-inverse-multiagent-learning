#!/bin/bash
set -euo pipefail
cd /home/user
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
for case in reference_existing reference_seed7 reference_seed8 reference_seed9 \
  stronger_training weaker_training shortcut_closed_form shortcut_label_copy \
  shortcut_cherry_pick shortcut_rewrite_labels shortcut_replace_fixed_data \
  shortcut_forged_scores_flags shortcut_constant shortcut_zero shortcut_negative \
  shortcut_empty shortcut_nan shortcut_inf shortcut_null
do
  echo "Audit case: $case"
  bash "redteam/$case/run.sh"
done
python -m redteam.summarize
