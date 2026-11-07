# Paper's Method

How the paper approaches the problem, i.e. the paper's core contributions.

## Key Contribution

The paper characterizes inverse Nash equilibrium computation as a min-max optimization problem and solves it with adversarial gradient descent-ascent. For concave games with convex regret in the unknown parameters, this gives polynomial-time inverse multiagent planning; the paper extends the idea to stochastic inverse multiagent learning and simulacral learning.

## Approach

For an observed equilibrium profile `x^\u2020`, the method minimizes exploitability over game parameters by solving `min_theta max_y psi(x^\u2020, y; theta)`, where `y` is an adversarial deviation profile and `psi` is cumulative regret. Algorithm 1 alternates projected gradient descent on `theta` and projected gradient ascent on `y`, using exact first-order gradients in the static planning case.

This reproduction specializes the inverse-planning min-max objective to static experiments from the paper. In Fisher markets, the market equilibrium is represented by the Eisenberg-Gale saddle objective. For Cobb-Douglas, linear, and Leontief utilities with known types, the unknown parameters are buyer budgets; the adversarial variable is the buyers' allocation deviation. The seller price-deviation component is included analytically but cancels for generated equilibria because the unit-supply market clears exactly. The default solver uses closed-form buyer best responses for the adversary and then descends on budgets; a one-step GDA adversary mode is also retained for Cobb-Douglas comparison.

For the Cobb-Douglas type-and-budget setting, the stabilizer recovers both budgets and per-buyer type shares. The implementation uses the same inverse-regret objective with exact Cobb-Douglas adversarial allocation best responses, gradient descent on budgets, and projected simplex descent on type shares through logits.

For the sampled-observation Cobb-Douglas setting (`fisher_cd_noisy_budget_recovery`), the observed behaviour is a set of noisy allocation samples at the posted prices. Following the paper's inverse multiagent learning objective (Corollary 1), the stabilizer minimizes the *expected* cumulative regret over the observed samples, `min_b max_Y E_k[psi(x_k, Y; b)]`, with a single destabilizer deviation chosen against that expectation. It is solved with the same projected descent on budgets, exact Cobb-Douglas best-response adversary, 5000 iterations and learning rate 0.01 (final iterate). The method rationalizes the samples as they are and does not model the measurement process, which is where it falls short of the achievable accuracy.

For Cournot duopoly games, the observed strategy is each firm's equilibrium quantity and the unknown parameter is marginal cost. The same inverse-regret objective minimizes the maximum unilateral profit improvement under the recovered cost. Linear inverse demand gives a closed-form adversarial best response for each firm, which is used inside projected descent on the cost.

Bertrand, Leontief and Cobb-Douglas type-plus-budget code paths remain in `method/` as unscored extensions (see `scoring/reference.json` -> `unscored_paper_results` for why they are not scored).

## Main Claims

Primary claim: adversarial inverse planning can recover parameters that rationalize observed equilibria in economic games, measured by high parameter recovery and low exploitability.

Secondary claims: the same min-max framing extends to stochastic Markov games and simulacral learning from sampled or lossy observations; on Spanish electricity data, the simulacrum improves MSE relative to ARIMA.
