#!/bin/bash
# Evaluation script — the standard way to evaluate work in this environment.
#
# This script must be SELF-CONTAINED using only code in eval/.
# Do NOT import from method/ — evaluate.sh must work even when the
# paper's method code is hidden from a scientist agent.
#
# Design it so that anyone following the same output format can run
# this script to evaluate their results.
#
# OUTPUT CONTRACT: This script MUST write scoring/scores.json containing
# a JSON dict nested by experiment, e.g.:
#   {"imagenet_classification": {"top1_accuracy": 82.1, "top5_accuracy": 94.8}}
# Experiment and metric names must match the keys in scoring/reference.json.
# This file is read by the system for automated comparison.
#
# Example usage:
#   ./evaluate.sh                                      # evaluate all available default artifacts
#   ./evaluate.sh --experiment fisher <predictions>    # evaluate one Fisher-market artifact
#   ./evaluate.sh --experiment cournot <predictions>   # evaluate one Cournot artifact
#
# Called from run.sh after training, or independently.

set -e

cd /home/user

mkdir -p scoring

if [ "$#" -eq 0 ]; then
  if [ -e artifacts/fisher_cd_budgets/predictions.jsonl ]; then
    python -m eval.evaluate_fisher --experiment-name fisher_cd_budget_recovery
  fi
  if [ -e artifacts/fisher_linear_budgets/predictions.jsonl ]; then
    python -m eval.evaluate_fisher --predictions artifacts/fisher_linear_budgets/predictions.jsonl --instances data/fisher_linear_budget_instances.jsonl --experiment-name fisher_linear_budget_recovery
  fi
  if [ -e artifacts/cournot_costs/predictions.jsonl ]; then
    python -m eval.evaluate_cournot
  fi
  if [ -e artifacts/bertrand_costs/predictions.jsonl ]; then
    python -m eval.evaluate_bertrand
  fi
elif [ "$1" = "--experiment" ]; then
  experiment="$2"
  shift 2
  case "$experiment" in
    fisher)
      if [ "$#" -eq 0 ]; then
        python -m eval.evaluate_fisher --experiment-name fisher_cd_budget_recovery
      else
        python -m eval.evaluate_fisher --predictions "$@"
      fi
      ;;
    cournot)
      if [ "$#" -eq 0 ]; then
        python -m eval.evaluate_cournot
      else
        python -m eval.evaluate_cournot --predictions "$@"
      fi
      ;;
    bertrand)
      if [ "$#" -eq 0 ]; then
        python -m eval.evaluate_bertrand
      else
        python -m eval.evaluate_bertrand --predictions "$@"
      fi
      ;;
    *)
      echo "Unknown experiment: $experiment" >&2
      exit 2
      ;;
  esac
else
  python -m eval.evaluate_fisher --predictions "$@"
fi
