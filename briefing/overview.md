# Overview

- **Paper ID:** 2502.14160
- **Title:** Efficient Inverse Multiagent Learning
- **Domain:** Game theory / inverse reinforcement learning / market modeling
- **TL;DR:** The paper formulates inverse game and inverse multiagent learning as adversarial min-max optimization to recover payoff parameters that make observed behavior an equilibrium.

## Short Summary

The paper studies how to infer unknown game parameters from observed equilibrium behavior. Its core construction minimizes exploitability of the observed behavior over parameters while an adversary searches for profitable deviations. The paper proves polynomial-time convergence for suitable concave games and extends the framework to stochastic Markov games and simulacral learning. Experiments include synthetic Fisher, Cournot, and Bertrand markets plus Spanish electricity price prediction.

## Key Results

- Static Cobb-Douglas Fisher budget recovery: 100% parameters recovered, average exploitability 0.0004.
- Static Cobb-Douglas Fisher type-and-budget recovery: 99.6% parameters recovered, average exploitability 0.0004.
- Static linear Fisher budget recovery: 100% parameters recovered, average exploitability 0.0018.
- Static Leontief Fisher budget recovery: 36.8% parameters recovered, average exploitability 0.2240.
- Cournot marginal-cost recovery: 95.2% parameters recovered, average exploitability 0.0000.
- Bertrand marginal-cost recovery: 78% parameters recovered, average exploitability 0.0011.
