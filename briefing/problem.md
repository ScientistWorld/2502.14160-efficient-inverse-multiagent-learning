# Problem Definition

## Research Question

Given observations of strategic behavior that is assumed to be an equilibrium of a parametric game whose parameters are unknown, recover game parameters under which the observed behavior is rational (an equilibrium), and that are close to the parameters that actually generated it.

The scored benchmarks are small synthetic economic games:

- **Fisher markets, exact observation** (3 buyers, 2 divisible goods with unit supply, known utility types, unknown buyer budgets). The observation is one competitive equilibrium: the price vector and every buyer's allocation. Two utility families are scored: Cobb-Douglas and linear.
- **Fisher markets, sampled observation** (Cobb-Douglas, same market size, known utility types, unknown budgets). The equilibrium prices are posted and observed exactly, but each buyer's equilibrium allocation is observed only through 16 independent noisy measurements. Each measured entry is the true equilibrium allocation multiplied by `exp(0.3 * z)` with `z ~ N(0, 1)` independent across samples, buyers and goods. The true equilibrium allocation is never shown.
- **Cournot duopoly** (known linear inverse demand `P(Q) = a + b Q`, common unknown marginal cost). The observation is the equilibrium production quantity of each firm.

## Why It Matters

Recovering payoff or market parameters from equilibrium behavior supports counterfactual prediction, preference estimation and economic model calibration when rewards or utilities are not directly observed. Real behavioral data is rarely an exact equilibrium: it is sampled and measured with noise, so a useful method has to rationalize the behavior it sees and still be accurate about the parameters behind it.

## Success Criteria

A successful solution estimates parameters close to the data-generating parameters (high recovery rate, low relative error, including in the worst cases) and keeps the true equilibrium behavior close to rational under those estimates (low exploitability). Parameter accuracy alone is not enough if the recovered game makes the equilibrium exploitable, and low exploitability alone is not enough if the parameters are wrong.
