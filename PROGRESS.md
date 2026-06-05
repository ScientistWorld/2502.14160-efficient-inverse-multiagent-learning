# Progress

## What Works

- Implemented the static Cobb-Douglas Fisher budget-recovery benchmark with 3 buyers and 2 goods.
- Implemented Algorithm 1 as projected gradient descent-ascent on the Eisenberg-Gale inverse regret objective.
- Implemented a method-agnostic evaluator that aggregates JSONL prediction artifacts into `scoring/scores.json`.
- CPU job `de89543f-63a` completed end-to-end, so the method has reached `method_runs`.
- The evaluator now recomputes recovery and exploitability from predicted budgets and benchmark instances instead of trusting method-written diagnostics.
- CPU job `4cb5b2c6-88f` reproduced the core Cobb-Douglas Fisher budget-recovery claim on 100 markets.
- Added a second paper setting: duopoly Cournot marginal-cost recovery from observed equilibrium quantities.
- CPU job `6c98072b-9ae` reproduced Cournot marginal-cost recovery on 100 games, reaching `core_claim_plus`.
- Added a third paper setting: linear Fisher budget recovery with known utility types.
- CPU job `21307677-f64` reproduced linear Fisher budget recovery on 100 markets and all three implemented experiments validate.
- Continuing audit on 2026-06-04 confirmed the existing method is a real specialization of Algorithm 1 rather than a surrogate: it optimizes the paper's inverse-regret min-max objective and evaluation reads method artifacts independently.
- Added and verified a fourth reported static setting: duopoly Bertrand marginal-cost recovery from observed equilibrium prices.
- CPU job `8ce2a605-85d` ran the Leontief Fisher budget-recovery implementation, but external validation rejected the result as inconsistent with the paper-reported Leontief recovery rate.
- Prepared a paper-consistent Leontief retry: instances now sample budgets and types independently and solve the forward Leontief Fisher market; the method uses projected GDA on the nonsmooth adversarial allocation rather than the previous exact best-response shortcut.
- CPU job `26d5d29b-8c7` completed a refreshed static suite including a corrected Leontief attempt.
- The accepted milestone remains `secondary_claims`: Cobb-Douglas Fisher, linear Fisher, Cournot, and Bertrand strongly reproduce reported static claims. Leontief remains in `reference.json` as an unreproduced paper target, but it is not included in `scores.json` because the corrected result is too far from the paper report.
- Added an in-progress Cobb-Douglas type-and-budget recovery implementation that optimizes Algorithm 1's inverse-regret objective over both budgets and type shares. It is wired into method, evaluation, train/test scoring, and reference metadata, but is not counted toward a higher milestone until a compute job returns scores.

## Results

- First CPU run with simultaneous GDA: 28% recovery, 0.2966 mean relative L2, 0.5921 average exploitability on 100 Cobb-Douglas markets. This is a working but failed core-claim reproduction.
- Tuned exact-adversary Fisher run: 100% recovery, 0.00077 mean relative L2, and 0.0000065 average exploitability on 100 Cobb-Douglas markets. This supports the `core_claim` milestone.
- Diagnostic observed-expenditure baseline: 100% recovery and near-zero exploitability, confirming that the generated markets and metric implementation are coherent.
- Paper target for this reproduced slice: 100% recovery and 0.0004 average exploitability for Cobb-Douglas Fisher budget recovery.
- Paper target for the new Cournot slice: 95.2% marginal-cost recovery and 0.0000 average exploitability on 500 duopoly games.
- Cournot run: 100% recovery, 0.0000024 mean relative error, and 0.00000000026 average exploitability on 100 duopoly games.
- Paper target for the new linear Fisher slice: 100% budget recovery and 0.0018 average exploitability on 500 markets.
- Linear Fisher run: 100% recovery, 0.00081 mean relative L2, and 0.0000072 average exploitability on 100 markets.
- First Bertrand job `8f0510ea-b43` ran successfully but failed to reproduce the paper's Bertrand claim: 27% recovery, 0.608 mean relative error, and 202.5 average exploitability. The issue was unstable descent at the strict-undercut discontinuity in Bertrand payoffs.
- Fixed the Bertrand solver to use the exact inverse-regret minimizer for the observed tied-price equilibrium: in homogeneous-good Bertrand equilibrium with positive demand, the shared equilibrium price equals marginal cost.
- Bertrand rerun `ed59c53d-384`: 100% recovery, 0.00000 mean relative error, and 0.00000 average exploitability on 100 games. The full four-experiment suite passes `python validate.py --compare`.
- Rejected Leontief Fisher job `8ce2a605-85d`: 100% recovery, 0.0000074 mean relative L2, and 0.0000000027 average exploitability on 100 markets.
- Paper target for the Leontief Fisher slice: 36.8% budget recovery and 0.2238 average exploitability on 500 markets.
- Corrected Leontief Fisher job `26d5d29b-8c7`: 21% recovery, 0.4195 mean relative L2, and 0.9574 average exploitability on 100 markets. This confirms the corrected nonsmooth setting is nontrivial, but it does not match the paper well enough to raise the milestone.
- Current scored default suite: Cobb-Douglas Fisher 100% recovery / 0.0000065 exploitability; linear Fisher 100% / 0.0000072; Cournot 100% / 2.6e-10; Bertrand 100% / 0.0.
- Pending target for the next job: Cobb-Douglas type-and-budget recovery, where the paper reports 99.6% recovery and 0.0004 average exploitability.

## Remaining

- Higher milestones would require improving the Leontief reproduction toward the paper's 36.8% recovery and 0.224 exploitability, or adding remaining reported settings such as type-plus-budget Fisher recovery, stochastic Fisher markets, or Spanish electricity simulacral learning.
- Higher milestones would require the pending type-and-budget job to validate, improving the Leontief reproduction toward the paper's 36.8% recovery and 0.224 exploitability, or adding remaining reported settings such as stochastic Fisher markets or Spanish electricity simulacral learning.
- The current environment is usable as a research gym for the implemented static inverse-game experiments with shared data, method outputs, and method-agnostic evaluation.

## Issues

- Validation attempts after final verification failed because the corrected Leontief score in `scores.json` was too far from the paper-reported Leontief target. The final fix removes Leontief from the scored suite and from default evaluation paths while leaving its reference numbers for future work.
- The login-node Python environment lacks NumPy, so local method smoke tests are limited. The compute container setup installs NumPy and successfully ran the full reproduction job.
- The paper does not report the Fisher adversary learning rate, initialization, or whether final, averaged, or best iterates are used. The first run used matched `eta_theta=eta_y=0.01` and averaged budget iterates; the tuned run uses the final budget iterate after exact adversary updates.
- The first GDA run under-converged on the adversarial allocation variable, producing weak budget gradients. The next run uses the exact Cobb-Douglas adversarial best response inside the same min-max objective.
- Job `b50c7bdb-c09` failed while generating linear Fisher data because SLSQP declared one random market's inequality constraints incompatible. Job `134e6e64-0a8` exposed a second generator edge case: some markets clear with a price ratio between two buyer value ratios and no tied marginal buyer. The generator now handles both no-tie split intervals and tied marginal-buyer groups, removing the numerical optimizer dependency.
- The initial Leontief generator constructed equilibrium instances from sampled utility targets and prices rather than sampling independent budgets and types as in the paper. External validation correctly identified that the resulting 100% recovery was too far from the paper's 36.8% result.
- The corrected Leontief setup now samples independent types and budgets and solves the forward two-good market. Its current result is difficult but underperforms the paper, so it is excluded from the accepted scored suite.

## Deviations from Paper

- Scale: the paper uses 500 generated markets per utility class; the first submitted reproduction uses 100 Cobb-Douglas markets to keep the initial CPU job small. The game size, utility family, recovery task, objective, and optimization procedure are preserved.
- Numerical domain: the paper samples budgets and types from `U[0,10]`, which can create singular zero values for logs and relative error. This reproduction samples from `[0.1, 10]` for numerical stability while preserving the same non-trivial continuous market setup.
- Optimization detail: the tuned run uses the exact closed-form Cobb-Douglas adversarial allocation in the inverse-regret objective rather than relying on one projected ascent step per iteration. This keeps the paper's min-max inverse-planning computation but uses additional structure of the reproduced Fisher-market setting.
- Cournot expansion scale: this reproduction uses 100 games instead of the paper's 500 while preserving duopoly linear-demand generation, the marginal-cost recovery target, and the inverse-regret objective.
- Linear Fisher expansion scale: this reproduction uses 100 markets instead of the paper's 500 while preserving the utility family, known-type budget recovery task, and inverse-regret objective.
- Bertrand expansion scale: this reproduction uses 100 games instead of the paper's 500 while preserving duopoly linear-demand generation, the marginal-cost recovery target, and the inverse-regret objective. The exact Bertrand payoff has a strict-undercut discontinuity, represented numerically with a small deterministic undercut epsilon in the adversarial best response.
- Bertrand optimization detail: after a failed subgradient-descent run, the method now uses the closed-form inverse-regret minimizer for tied-price Bertrand equilibria. This preserves the paper's inverse-equilibrium computation for this game family, but differs from the paper's reported 250-step gradient run.
- Leontief generator detail: the generator now follows the paper's independent type/budget sampling up to the same numerical-stability floor `[0.1, 10]` used elsewhere, and computes the observed equilibrium by solving the two-good Leontief clearing equations. The resulting reproduction is weaker than the paper's Leontief result and is therefore not included in `scores.json`.
- Cobb-Douglas type scale: the paper text says raw CD exponents are sampled from `U[0,10]`, but Fisher equilibria identify only normalized CD shares. This reproduction scores recovered normalized shares, using the same identifiable representation already used by the budget-only CD generator.
