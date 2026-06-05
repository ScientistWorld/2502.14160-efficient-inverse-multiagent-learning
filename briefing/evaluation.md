# Evaluation

## Metrics

The benchmark reports `parameter_recovery_rate`, the fraction of instances whose relative parameter error is at most 0.1; a mean relative-error metric (`mean_relative_l2` for vector budgets and `mean_relative_error` for scalar costs); tail-error metrics (`p90_relative_l2` or `p90_relative_error`); `average_exploitability`; and `max_exploitability`. Higher recovery rate is better. Lower relative error and exploitability are better.

## Baselines and Targets

For static Cobb-Douglas Fisher markets with known utility types and unknown budgets, the paper reports 100% parameter recovery and average exploitability 0.0004 over 500 markets. For static linear Fisher markets with known utility types and unknown budgets, it reports 100% recovery and average exploitability 0.0018. For Cournot duopoly games with unknown marginal cost, the paper reports 95.2% parameter recovery and average exploitability 0.0000 over 500 games. For Bertrand duopoly games with unknown marginal cost, it reports 78% recovery and average exploitability 0.0011 over 500 games. This reproduction uses the same game structures and smaller generated sets for runnable benchmark jobs. The paper's Leontief and Cobb-Douglas type-plus-budget Fisher settings remain in `scoring/reference.json` as unreproduced targets.

## Evaluation Protocol

Run a method to write JSONL predictions with one row per benchmark instance, including estimated parameters. Then run `scripts/evaluate.sh`, or pass an explicit experiment selector (`fisher`, `cournot`, `bertrand`, or development-only selectors such as `leontief` and `fisher_cd_type_budget`) with a prediction path. The default evaluator aggregates available scored experiments and writes `scoring/scores.json`. It imports only `eval/` and `data/` code and reads method artifacts, so future methods can be scored by matching the same output formats.
