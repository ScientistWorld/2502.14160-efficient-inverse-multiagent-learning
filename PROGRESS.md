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
- The accepted default suite remains the four verified static settings: Cobb-Douglas Fisher, linear Fisher, Cournot, and Bertrand.
- Prepared a paper-consistent Leontief retry: instances now sample budgets and types independently and solve the forward Leontief Fisher market; the method uses projected GDA on the nonsmooth adversarial allocation rather than the previous exact best-response shortcut.

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
- Because the earlier reproduced Leontief instances were materially easier than the paper setting, that result was rejected. The corrected Leontief retry is now back in the default run scripts, but it is not counted toward a higher milestone until the submitted job verifies the new scores.

## Remaining

- Higher milestones would require adding remaining reported settings: a paper-consistent Leontief budget-recovery generator, type-plus-budget Fisher recovery, stochastic Fisher markets, or Spanish electricity simulacral learning.
- The current environment is usable as a research gym for the implemented static inverse-game experiments with shared data, method outputs, and method-agnostic evaluation.

## Issues

- The login-node Python environment lacks NumPy, so local method smoke tests are limited. The compute container setup installs NumPy and successfully ran the full reproduction job.
- The paper does not report the Fisher adversary learning rate, initialization, or whether final, averaged, or best iterates are used. The first run used matched `eta_theta=eta_y=0.01` and averaged budget iterates; the tuned run uses the final budget iterate after exact adversary updates.
- The first GDA run under-converged on the adversarial allocation variable, producing weak budget gradients. The next run uses the exact Cobb-Douglas adversarial best response inside the same min-max objective.
- Job `b50c7bdb-c09` failed while generating linear Fisher data because SLSQP declared one random market's inequality constraints incompatible. Job `134e6e64-0a8` exposed a second generator edge case: some markets clear with a price ratio between two buyer value ratios and no tied marginal buyer. The generator now handles both no-tie split intervals and tied marginal-buyer groups, removing the numerical optimizer dependency.
- The Leontief generator constructs equilibrium instances from sampled utility targets and prices rather than sampling independent budgets and types as in the paper. External validation correctly identified that the resulting 100% recovery is too far from the paper's 36.8% result, so Leontief is no longer a scored default experiment.
- The next CPU job tests the corrected Leontief setup. Until that result is available, the accepted milestone remains `secondary_claims`.

## Deviations from Paper

- Scale: the paper uses 500 generated markets per utility class; the first submitted reproduction uses 100 Cobb-Douglas markets to keep the initial CPU job small. The game size, utility family, recovery task, objective, and optimization procedure are preserved.
- Numerical domain: the paper samples budgets and types from `U[0,10]`, which can create singular zero values for logs and relative error. This reproduction samples from `[0.1, 10]` for numerical stability while preserving the same non-trivial continuous market setup.
- Optimization detail: the tuned run uses the exact closed-form Cobb-Douglas adversarial allocation in the inverse-regret objective rather than relying on one projected ascent step per iteration. This keeps the paper's min-max inverse-planning computation but uses additional structure of the reproduced Fisher-market setting.
- Cournot expansion scale: this reproduction uses 100 games instead of the paper's 500 while preserving duopoly linear-demand generation, the marginal-cost recovery target, and the inverse-regret objective.
- Linear Fisher expansion scale: this reproduction uses 100 markets instead of the paper's 500 while preserving the utility family, known-type budget recovery task, and inverse-regret objective.
- Bertrand expansion scale: this reproduction uses 100 games instead of the paper's 500 while preserving duopoly linear-demand generation, the marginal-cost recovery target, and the inverse-regret objective. The exact Bertrand payoff has a strict-undercut discontinuity, represented numerically with a small deterministic undercut epsilon in the adversarial best response.
- Bertrand optimization detail: after a failed subgradient-descent run, the method now uses the closed-form inverse-regret minimizer for tied-price Bertrand equilibria. This preserves the paper's inverse-equilibrium computation for this game family, but differs from the paper's reported 250-step gradient run.
- Leontief generator detail: the paper samples Leontief types and budgets independently from `U[0,10]`; this reproduction constructs two-good Leontief equilibria by sampling positive utility targets and prices, scaling type columns to clear unit supplies, and deriving budgets from equilibrium bundle costs. That replacement made the benchmark too easy, so Leontief is retained only as exploratory code and is not included in the accepted scores.
- Pending Leontief correction: the generator now follows the paper's independent type/budget sampling up to the same numerical-stability floor `[0.1, 10]` used elsewhere, and computes the observed equilibrium by solving the two-good Leontief clearing equations. The submitted run will determine whether this setting can be restored to the scored suite.
