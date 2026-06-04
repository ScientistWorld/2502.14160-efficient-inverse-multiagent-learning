# Reproduction Milestones

**Current: core_claim_plus**

<!-- Milestone levels (update "Current" above as you progress):
  none             — just started, no meaningful progress yet
  method_runs      — the paper's method executes end-to-end without errors
  core_claim       — minimum experiment supports the paper's central claim
  core_claim_plus  — core claim reproduced on additional settings
  secondary_claims — secondary results or contributions reproduced
  majority         — more than half of reported results reproduced
  near_complete    — most results reproduced, only minor gaps remain
  full             — all reported results reproduced
-->

## Progress Log

### [2026-06-04 23:45] - none
- Read the paper's inverse-game formulation, Algorithm 1, and static Fisher market experiments.
- Implemented a first CPU reproduction target for Cobb-Douglas Fisher budget recovery using the paper's adversarial min-max inverse-planning objective.
- Added method, baseline, evaluation, scoring reference, scripts, and briefing documentation.

### [2026-06-05 00:10] - method_runs
- CPU job `de89543f-63a` completed without errors and wrote method artifacts plus `scoring/scores.json`.
- The first simultaneous GDA configuration reached only 28% recovery and average exploitability 0.5921, so it does not support the core claim yet.
- Updated the solver to use the exact Cobb-Douglas adversarial best response for the same inverse-regret min-max objective and tightened evaluation to recompute metrics from predictions and benchmark data.

### [2026-06-05 00:35] - core_claim
- CPU job `4cb5b2c6-88f` completed without errors after the exact-adversary Fisher update.
- Reproduced the paper's Cobb-Douglas Fisher budget-recovery claim on 100 markets: 100% recovery, mean relative L2 0.00077, and average exploitability 0.0000065.
- Added a Cournot marginal-cost recovery experiment for the next expansion job.

### [2026-06-05 00:45] - core_claim_plus
- CPU job `6c98072b-9ae` completed without errors and reproduced a second paper setting.
- Cournot marginal-cost recovery on 100 duopoly games reached 100% recovery, mean relative error 0.0000024, and average exploitability 0.00000000026.
- Added the paper's linear Fisher budget-recovery setting for the next expansion job.

## Stop Justification
- Not stopped; a CPU expansion job is being submitted to test linear Fisher budget recovery.
