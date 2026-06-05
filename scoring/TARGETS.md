# Evaluation Targets

Optimize `fisher_cd_budget_recovery` first, then `cournot_cost_recovery`, `fisher_linear_budget_recovery`, `fisher_leontief_budget_recovery`, and `bertrand_cost_recovery`.

Primary target: maximize `parameter_recovery_rate`, the share of markets whose recovered budgets are within relative L2 error 0.1 of the generating budgets.

Constraint targets: minimize `average_exploitability` and `mean_relative_l2`. A method that recovers numbers close to the hidden budgets but leaves the observed allocation-price profile exploitable has not solved the inverse-equilibrium problem.

For `cournot_cost_recovery`, maximize the share of games whose recovered marginal cost is within relative error 0.1 of the generating cost. Constraint targets are low average exploitability under the recovered cost and low mean relative error.

For `fisher_linear_budget_recovery`, maximize the share of markets whose recovered budgets are within relative L2 error 0.1 of the generating budgets. Constraint targets are low average exploitability and low mean relative L2 error.

For `fisher_leontief_budget_recovery`, maximize the share of markets whose recovered budgets are within relative L2 error 0.1 of the generating budgets. Constraint targets are low average exploitability and low mean relative L2 error. This setting is intentionally harder because Leontief utilities are nonsmooth and may not identify the true budgets from a single observed equilibrium.

For `bertrand_cost_recovery`, maximize the share of games whose recovered marginal cost is within relative error 0.1 of the generating cost. Constraint targets are low average exploitability under the recovered cost and low mean relative error.
