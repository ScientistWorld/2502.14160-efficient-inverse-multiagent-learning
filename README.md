# Efficient Inverse Multiagent Learning

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2502.14160"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2502.14160-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| | |
|---|---|
| **Paper ID** | [2502.14160](https://arxiv.org/abs/2502.14160) |
| **Domain** | Game theory / inverse reinforcement learning / market modeling |
| **TL;DR** | The paper formulates inverse game and inverse multiagent learning as adversarial min-max optimization to recover payoff parameters that make observed behavior an equilibrium. |

## Summary

The paper studies how to infer unknown game parameters from observed equilibrium behavior. Its core construction minimizes exploitability of the observed behavior over parameters while an adversary searches for profitable deviations. The paper proves polynomial-time convergence for suitable concave games and extends the framework to stochastic Markov games and simulacral learning. Experiments include synthetic Fisher, Cournot, and Bertrand markets plus Spanish electricity price prediction.

## Problem

Given observations of strategic behavior that are assumed to be an equilibrium of an unknown parametric game, recover game parameters for which the observed behavior is rational. In the scored static benchmarks, the tasks are to recover buyer budgets in synthetic Cobb-Douglas or linear Fisher markets and recover marginal production costs in synthetic Cournot and Bertrand duopoly games from observed equilibrium quantities or prices.

## The paper's method

The paper characterizes inverse Nash equilibrium computation as a min-max optimization problem and solves it with adversarial gradient descent-ascent. For concave games with convex regret in the unknown parameters, this gives polynomial-time inverse multiagent planning; the paper extends the idea to stochastic inverse multiagent learning and simulacral learning.

## Key results of the paper

- Static Cobb-Douglas Fisher budget recovery: 100% parameters recovered, average exploitability 0.0004.
- Static Cobb-Douglas Fisher type-and-budget recovery: 99.6% parameters recovered, average exploitability 0.0004.
- Static linear Fisher budget recovery: 100% parameters recovered, average exploitability 0.0018.
- Static Leontief Fisher budget recovery: 36.8% parameters recovered, average exploitability 0.2240.
- Cournot marginal-cost recovery: 95.2% parameters recovered, average exploitability 0.0000.

## Leaderboard

FNI of AI scientists on this paper, grader-verified. 0 matches the paper's method, higher is better.

| Model | Innovate |
|---|---:|
| `glm-5.2-xhigh` | +100.0 |
| `gpt-5.6-luna-xhigh` | +100.0 |
| `gpt-5.6-sol-xhigh` | +100.0 |
| `gpt-5.6-terra-xhigh` | +100.0 |
| `gpt-5.5-xhigh` | +100.0 |

`innovate`: the model designs its own method. `improve`: it starts from the paper's method.

## Run it

```bash
pip install sciworld
sw research 2502.14160 --mode innovate --agent claude-code
sw evaluate 2502.14160
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

