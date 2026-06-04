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

### [2026-06-04 23:58] - core_claim_plus
- Audited the inherited reproduction and confirmed that the implemented Fisher and Cournot methods solve the paper's inverse-regret min-max objective rather than a surrogate.
- Added duopoly Bertrand marginal-cost recovery code, method-agnostic evaluation, scripts, and paper reference targets.
- Submitted a CPU test job to run the full four-experiment reproduction in the container.

### [2026-06-05 00:04] - core_claim_plus
- Job `8f0510ea-b43` completed, confirming the four-experiment script runs in the container.
- The first Bertrand subgradient solver produced poor results, so the milestone was not raised.
- Replaced the unstable Bertrand subgradient path for tied equilibrium prices with the exact inverse-regret minimizer and submitted a follow-up CPU test job.

## Stop Justification
- Current confirmed milestone remains `core_claim_plus` until the Bertrand job finishes.
- Remaining paper settings after Bertrand include Leontief Fisher markets, type-plus-budget recovery, stochastic Fisher markets, and Spanish electricity simulacral learning.
