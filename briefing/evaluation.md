# Evaluation

How success is measured. Describe only the metrics, targets, and evaluation procedure — do NOT describe the paper's method or how they achieved these results. Think of this as a general evaluation protocal for other scientists trying to solve the same problem, where they should not see this paper's solution.

## Metrics

The benchmark reports `parameter_recovery_rate`, the fraction of instances whose relative parameter error is at most 0.1; a mean relative-error metric (`mean_relative_l2` for vector budgets and `mean_relative_error` for scalar costs); and `average_exploitability`, the average maximum unilateral-deviation regret of the observed equilibrium under recovered parameters. Higher recovery rate is better. Lower relative error and exploitability are better.

## Baselines and Targets

For static Cobb-Douglas Fisher markets with known utility types and unknown budgets, the paper reports 100% parameter recovery and average exploitability 0.0004 over 500 markets. For static linear Fisher markets with known utility types and unknown budgets, it reports 100% recovery and average exploitability 0.0018. For Cournot duopoly games with unknown marginal cost, the paper reports 95.2% parameter recovery and average exploitability 0.0000 over 500 games. This reproduction uses the same game structures and smaller generated sets for runnable benchmark jobs.

## Evaluation Protocol

Run a method to write JSONL predictions with one row per benchmark instance, including estimated parameters. Then run `scripts/evaluate.sh`, or pass `--experiment fisher` or `--experiment cournot` with a prediction path. The evaluator aggregates metrics and writes `scoring/scores.json`. It imports only `eval/` and `data/` code and reads method artifacts, so future methods can be scored by matching the same output formats.
