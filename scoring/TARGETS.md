# Evaluation Targets

Optimize `fisher_cd_budget_recovery`.

Primary target: maximize `parameter_recovery_rate`, the share of markets whose recovered budgets are within relative L2 error 0.1 of the generating budgets.

Constraint targets: minimize `average_exploitability` and `mean_relative_l2`. A method that recovers numbers close to the hidden budgets but leaves the observed allocation-price profile exploitable has not solved the inverse-equilibrium problem.
