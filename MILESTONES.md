# Reproduction Milestones

**Current: secondary_claims**

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
- This claim was later rejected by stricter paper-consistency validation because the Leontief result was too far from the paper report.

### [2026-06-05 00:32] - secondary_claims
- External validation rejected the Leontief score because this reproduction's constructed Leontief instances produced 100% recovery while the paper reports 36.8%, a gap too large to accept as the same result.
- Removed Leontief from the default scored suite and restored the milestone to the verified four-experiment static subset.
- `scoring/scores.json` now reports Cobb-Douglas Fisher, linear Fisher, Cournot, and Bertrand results only.

### [2026-06-05 00:45] - secondary_claims
- Reworked the Leontief Fisher budget-recovery path for a new verification job.
- The generator now samples Leontief types and budgets independently and solves the forward two-good competitive equilibrium.
- The method now runs projected GDA for Leontief adversarial allocations, preserving the paper's nonsmooth Algorithm 1 procedure instead of using the earlier exact best-response shortcut.

### [2026-06-05 01:05] - secondary_claims
- CPU job `26d5d29b-8c7` completed successfully and refreshed `scoring/scores.json` for five static experiments.
- The corrected Leontief slice is no longer artificially easy: it scored 21% recovery and 0.9574 average exploitability, below the paper's 36.8% and 0.2240.
- Final verification kept the milestone at `secondary_claims`: four static settings reproduce strongly, and Leontief is retained as a difficult scored setting rather than used to claim a higher milestone.

## Stop Justification
- Final verification completed. The workspace is ready as a research gym at `secondary_claims` with four validated scored experiments; Leontief remains an unreproduced reference target for future work.
