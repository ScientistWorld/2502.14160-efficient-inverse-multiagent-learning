# Progress

## What Works

- Implemented the static Cobb-Douglas Fisher budget-recovery benchmark with 3 buyers and 2 goods.
- Implemented Algorithm 1 as projected gradient descent-ascent on the Eisenberg-Gale inverse regret objective.
- Implemented a method-agnostic evaluator that aggregates JSONL prediction artifacts into `scoring/scores.json`.
- CPU job `de89543f-63a` completed end-to-end, so the method has reached `method_runs`.
- The evaluator now recomputes recovery and exploitability from predicted budgets and benchmark instances instead of trusting method-written diagnostics.

## Results

- First CPU run with simultaneous GDA: 28% recovery, 0.2966 mean relative L2, 0.5921 average exploitability on 100 Cobb-Douglas markets. This is a working but failed core-claim reproduction.
- Diagnostic observed-expenditure baseline: 100% recovery and near-zero exploitability, confirming that the generated markets and metric implementation are coherent.
- Paper target for this reproduced slice: 100% recovery and 0.0004 average exploitability for Cobb-Douglas Fisher budget recovery.

## Remaining

- Run the tuned exact-adversary inverse-planning job and inspect `scoring/scores.json`.
- If the tuned method supports the core claim, update milestone to `core_claim`; otherwise tune initialization, steps, or projection while preserving the paper's inverse-regret min-max objective.
- Potential expansion: add linear Fisher budget recovery or Cournot marginal-cost recovery.

## Issues

- The login-node Python environment lacks NumPy, so only structural validation was run locally. The container setup installs NumPy for compute jobs.
- The paper does not report the Fisher adversary learning rate, initialization, or whether final, averaged, or best iterates are used. The first run used matched `eta_theta=eta_y=0.01` and averaged budget iterates; the tuned run uses the final budget iterate after exact adversary updates.
- The first GDA run under-converged on the adversarial allocation variable, producing weak budget gradients. The next run uses the exact Cobb-Douglas adversarial best response inside the same min-max objective.

## Deviations from Paper

- Scale: the paper uses 500 generated markets per utility class; the first submitted reproduction uses 100 Cobb-Douglas markets to keep the initial CPU job small. The game size, utility family, recovery task, objective, and optimization procedure are preserved.
- Numerical domain: the paper samples budgets and types from `U[0,10]`, which can create singular zero values for logs and relative error. This reproduction samples from `[0.1, 10]` for numerical stability while preserving the same non-trivial continuous market setup.
- Optimization detail: the tuned run uses the exact closed-form Cobb-Douglas adversarial allocation in the inverse-regret objective rather than relying on one projected ascent step per iteration. This keeps the paper's min-max inverse-planning computation but uses additional structure of the reproduced Fisher-market setting.
