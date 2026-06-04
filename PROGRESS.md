# Progress

## What Works

- Implemented the static Cobb-Douglas Fisher budget-recovery benchmark with 3 buyers and 2 goods.
- Implemented Algorithm 1 as projected gradient descent-ascent on the Eisenberg-Gale inverse regret objective.
- Implemented a method-agnostic evaluator that aggregates JSONL prediction artifacts into `scoring/scores.json`.
- `python validate.py` passes for the staged workspace.

## Results

- No compute-node results yet. A CPU job is being submitted to run 100 generated markets for the method and baseline.
- Paper target for this reproduced slice: 100% recovery and 0.0004 average exploitability for Cobb-Douglas Fisher budget recovery.

## Remaining

- Run the submitted CPU job and inspect `scoring/scores.json`.
- If the method supports the core claim, update milestone to `core_claim`; otherwise tune initialization, steps, or projection while preserving Algorithm 1.
- Potential expansion: add linear Fisher budget recovery or Cournot marginal-cost recovery.

## Issues

- The login-node Python environment lacks NumPy, so only structural validation was run locally. The container setup installs NumPy for compute jobs.
- The paper does not report the Fisher adversary learning rate, initialization, or whether final, averaged, or best iterates are used. This implementation uses matched `eta_theta=eta_y=0.01` and returns the time-average of budget iterates, consistent with the theorem.

## Deviations from Paper

- Scale: the paper uses 500 generated markets per utility class; the first submitted reproduction uses 100 Cobb-Douglas markets to keep the initial CPU job small. The game size, utility family, recovery task, objective, and optimization procedure are preserved.
- Numerical domain: the paper samples budgets and types from `U[0,10]`, which can create singular zero values for logs and relative error. This reproduction samples from `[0.1, 10]` for numerical stability while preserving the same non-trivial continuous market setup.
