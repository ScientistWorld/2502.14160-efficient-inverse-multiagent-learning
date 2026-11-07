# Experiments

## fisher_cd_budget_recovery

Can a method recover hidden buyer budgets from one exactly observed competitive equilibrium (prices and allocations) of a small Cobb-Douglas Fisher market with known utility types? It measures parameter accuracy and whether the true equilibrium remains unexploitable under the recovered budgets. It reproduces a setting reported in the paper. Strong methods already sit near the bound here, so it mainly guards against regressions.

## fisher_linear_budget_recovery

The same question for small linear-utility Fisher markets, whose demands are corner solutions rather than smooth interior choices. It reproduces a setting reported in the paper and also mainly guards against regressions.

## cournot_cost_recovery

Can a method recover a duopoly's hidden marginal production cost from observed equilibrium quantities and a known linear inverse demand? It measures cost accuracy and whether the observed quantities stay an equilibrium under the recovered cost. It reproduces a setting reported in the paper and mainly guards against regressions.

## fisher_cd_noisy_budget_recovery

Can a method recover hidden buyer budgets when equilibrium behavior is only *sampled*? Prices are posted exactly, but each market's allocations are seen only through 16 noisy measurements, and the true equilibrium allocation is never shown. It measures how accurately the budgets are estimated (recovery rate, mean and tail error) and whether the true equilibrium is rational under them (exploitability). Accuracy is limited by noise, not by an exact identity, so this experiment separates methods that use the observations well from methods that do not, and it carries the largest weight.
