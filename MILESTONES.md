# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-06-04 23:23] - none
- Read the paper and identified the core static inverse-game experiments: Fisher market budget recovery and Cournot marginal-cost recovery.
- Set up the workspace structure for briefing, method, data, evaluation, scripts, and scoring.

### [2026-06-04 23:31] - method_runs
- Implemented Algorithm 1, adversarial inverse multiagent planning, for static Cobb-Douglas Fisher markets.
- Added synthetic Fisher market generation, method outputs, and method-agnostic evaluation.
- Completed an end-to-end CPU job that generated data, ran the method, and wrote `scoring/scores.json`.

### [2026-06-04 23:38] - core_claim
- Tuned the Fisher inverse-regret optimizer using an exact adversarial best-response oracle for the same min-max objective.
- Reproduced the paper's core Cobb-Douglas Fisher budget-recovery claim on 100 generated markets: 100% recovery with near-zero average exploitability.

### [2026-06-04 23:49] - core_claim_plus
- Added duopoly Cournot marginal-cost recovery from observed equilibrium quantities.
- Added linear Fisher budget recovery with known utility types.
- Completed CPU jobs for all three implemented settings and validated the workspace with `python validate.py --compare`.
- Reproduced all three implemented settings with 100% recovery and low exploitability on 100 instances each.

## Stop Justification
- Completed at milestone `core_claim_plus`: the environment implements the paper's actual Algorithm 1 min-max inverse planning objective for three reported static economic settings, scores both recovery and exploitability constraints, and passes structural validation.
- Remaining paper settings, including Leontief Fisher markets, type-plus-budget recovery, Bertrand competition, and Spanish electricity simulacral learning, are not implemented.
