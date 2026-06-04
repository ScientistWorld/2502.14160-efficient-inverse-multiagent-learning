# Reproduction Milestones

**Current: method_runs**

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

## Stop Justification
- Not stopped; tuned compute job is being submitted to test whether the core claim is supported.
