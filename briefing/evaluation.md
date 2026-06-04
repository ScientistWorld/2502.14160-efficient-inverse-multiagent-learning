# Evaluation

How success is measured. Describe only the metrics, targets, and evaluation procedure — do NOT describe the paper's method or how they achieved these results. Think of this as a general evaluation protocal for other scientists trying to solve the same problem, where they should not see this paper's solution.

## Metrics

The benchmark reports `parameter_recovery_rate`, the fraction of instances whose relative parameter error is at most 0.1 in L2 norm; `mean_relative_l2`, the average relative parameter error; and `average_exploitability`, the average maximum unilateral-deviation regret of the observed equilibrium under recovered parameters. Higher recovery rate is better. Lower relative error and exploitability are better.

## Baselines and Targets

For static Cobb-Douglas Fisher markets with known utility types and unknown budgets, the paper reports 100% parameter recovery and average exploitability 0.0004 over 500 markets. This reproduction uses the same 3-buyer, 2-good structure and a smaller generated set for the first runnable benchmark.

## Evaluation Protocol

Run a method to write JSONL predictions with one row per market instance, including estimated budgets and per-instance exploitability. Then run `scripts/evaluate.sh <predictions.jsonl>`, which aggregates metrics and writes `scoring/scores.json`. The evaluator imports only `eval/` code and reads method artifacts, so future methods can be scored by matching the same output format.
