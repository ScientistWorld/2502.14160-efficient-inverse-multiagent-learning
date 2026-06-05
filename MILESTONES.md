# Reproduction Milestones

**Current: majority**

## Progress Log

### [2026-06-05 00:03] - secondary_claims
- Verified prior completed jobs reproduce four reported static inverse-game settings: Cobb-Douglas Fisher budget recovery, linear Fisher budget recovery, Cournot cost recovery, and Bertrand cost recovery.
- Validation passes with method-agnostic evaluation and exploitability constraints.
- Added Leontief Fisher budget recovery code and scoring for the next CPU job, but did not count it toward the milestone before job results.

### [2026-06-05 00:12] - secondary_claims
- Continuing audit restored `secondary_claims` after checking that the implemented static methods are real Algorithm 1 inverse-regret specializations, not surrogates.
- Found one incomplete deliverable from the prior turn: `fisher_leontief_budget_recovery` is in `reference.json` and targets but not yet in `scores.json`.
- Prepared to resubmit the CPU verification job to generate fresh scores including Leontief.

### [2026-06-05 00:16] - majority
- CPU job `8ce2a605-85d` completed successfully and regenerated the full static suite.
- `scoring/scores.json` now includes five reproduced reported settings: Cobb-Douglas, linear, and Leontief Fisher budget recovery plus Cournot and Bertrand cost recovery.
- `python validate.py --compare` passes with method-agnostic evaluation, exploitability constraints, and no `eval/` imports from `method/`.

## Stop Justification
- The packaged environment reaches `majority`: five reported static inverse-game settings are reproduced and validated. Remaining unreproduced paper results are the harder type-plus-budget Fisher variants and Spanish electricity simulacral-learning study.
