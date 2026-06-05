# Paper's Method

How the paper approaches the problem, i.e. the paper's core contributions.

## Key Contribution

The paper characterizes inverse Nash equilibrium computation as a min-max optimization problem and solves it with adversarial gradient descent-ascent. For concave games with convex regret in the unknown parameters, this gives polynomial-time inverse multiagent planning; the paper extends the idea to stochastic inverse multiagent learning and simulacral learning.

## Approach

For an observed equilibrium profile `x^\u2020`, the method minimizes exploitability over game parameters by solving `min_theta max_y psi(x^\u2020, y; theta)`, where `y` is an adversarial deviation profile and `psi` is cumulative regret. Algorithm 1 alternates projected gradient descent on `theta` and projected gradient ascent on `y`, using exact first-order gradients in the static planning case.

This reproduction specializes the inverse-planning min-max objective to static experiments from the paper. In Fisher markets, the market equilibrium is represented by the Eisenberg-Gale saddle objective. For Cobb-Douglas, linear, and Leontief utilities with known types, the unknown parameters are buyer budgets; the adversarial variable is the buyers' allocation deviation. The seller price-deviation component is included analytically but cancels for generated equilibria because the unit-supply market clears exactly. The default solver uses closed-form buyer best responses for the adversary and then descends on budgets; a one-step GDA adversary mode is also retained for Cobb-Douglas comparison.

For the Cobb-Douglas type-and-budget setting, the stabilizer recovers both budgets and per-buyer type shares. The implementation uses the same inverse-regret objective with exact Cobb-Douglas adversarial allocation best responses, gradient descent on budgets, and projected simplex descent on type shares through logits.

For Cournot duopoly games, the observed strategy is each firm's equilibrium quantity and the unknown parameter is marginal cost. The same inverse-regret objective minimizes the maximum unilateral profit improvement under the recovered cost. Linear inverse demand gives a closed-form adversarial best response for each firm, which is used inside projected descent on the cost.

For Bertrand duopoly games, the observed strategy is each firm's equilibrium price and the unknown parameter is marginal cost. The method again minimizes cumulative unilateral-deviation regret under linear demand, using the price-setting adversarial best response inside projected descent on marginal cost.

## Main Claims

Primary claim: adversarial inverse planning can recover parameters that rationalize observed equilibria in economic games, measured by high parameter recovery and low exploitability.

Secondary claims: the same min-max framing extends to stochastic Markov games and simulacral learning from sampled or lossy observations; on Spanish electricity data, the simulacrum improves MSE relative to ARIMA.
