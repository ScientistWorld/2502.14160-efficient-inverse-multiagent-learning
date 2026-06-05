# Problem Definition

What problem does this paper address? Write this so that someone with no knowledge of the paper can understand what needs to be solved and how success is measured.

Do NOT describe the paper's method or solution here — only the problem itself. Think about if a future scientist agent try to solve this problem from scratch without knowing what approach the paper took. If you leak the solution, you compromise the benchmark.

## Research Question

Given observations of strategic behavior that are assumed to be an equilibrium of an unknown parametric game, recover game parameters for which the observed behavior is rational. In the static market benchmarks, the tasks are to recover buyer budgets in synthetic Cobb-Douglas, linear, or Leontief Fisher markets from observed competitive-equilibrium allocations and prices, and to recover marginal production costs in synthetic Cournot and Bertrand duopoly games from observed equilibrium quantities or prices.

## Why It Matters

Recovering payoff or market parameters from equilibrium behavior supports counterfactual prediction, preference estimation, and economic model calibration when rewards or utilities are not directly observed.

## Success Criteria

A successful solution estimates parameters close to the data-generating parameters and keeps the observed behavior close to equilibrium under those estimates. Parameter recovery alone is insufficient if the recovered game assigns high exploitability to the observed behavior.
