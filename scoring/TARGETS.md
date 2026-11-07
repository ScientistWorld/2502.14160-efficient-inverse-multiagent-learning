# Evaluation Targets

All four experiments are scored on the hidden test split; `fisher_cd_noisy_budget_recovery` carries weight 0.4 and the other three 0.2 each.

## Primary target

- `fisher_cd_noisy_budget_recovery`: maximize `parameter_recovery_rate` (share of held-out markets whose recovered budgets are within relative L2 error 0.1) and minimize `mean_relative_l2` when allocations are observed only through noisy samples. Reference: 60.5% recovery, mean relative L2 0.093. Simple observed-expenditure baseline: 34%, 0.127. This is where research gains show up.

## Constraint targets (must hold while improving the primary target)

- `fisher_cd_noisy_budget_recovery`: keep `average_exploitability` and `max_exploitability` of the true equilibrium under the recovered budgets low (reference 0.024 / 0.188), and keep the tail error `p90_relative_l2` low (reference 0.143).
- `fisher_cd_budget_recovery`, `fisher_linear_budget_recovery`: keep 100% budget recovery, mean relative L2 near 1e-3 or better, and average exploitability near 1e-5 or better (paper: 100% / 0.0004 and 100% / 0.0018).
- `cournot_cost_recovery`: keep 100% cost recovery, mean relative error near 3e-6 or better and near-zero exploitability (paper: 95.2% / 0.0000).
- Every experiment must have valid predictions for every instance; a missing, duplicated, non-finite or out-of-domain prediction scores that experiment as failed.
