# Hardening report

**Does a better result now score higher? Yes.** A genuinely better estimator on the new sampled-observation experiment ranks **+0.165** above the reference, about 80 times the reference's seed spread. A one-step (weaker) run ranks **−18.57**. The supplied simple baseline now ranks clearly below the reference (−0.136), and its single-sample variant even lower (−1.05). Before hardening, the simple baseline *beat* the reference (+0.0006). The 4×-longer (stronger) run still ranks above the reference (+0.0005), but this numerical-precision gain is now below the seed spread (see "Could not fix").

Every shortcut that paid in `REDTEAM.md` now scores as failed or exactly ties the reference.

All numbers come from CPU job `7b7d5879-566`, run by `python -m redteam.hardening.runner`. Each case's predictions were installed in the workspace and scored by `bash scripts/evaluate_test.sh` (and `evaluate_train.sh`) with **no arguments**, in a fresh process; the workspace was then restored. Rank change = Σ_exp weight × Σ_metric coefficient × (candidate − reference), with the weights and coefficients of the final `scoring/reference.json`; the reference is the shipped seed-7 run. Per-case scores, logs and status are in `redteam/hardening/cases/<case>/`. The full table is `redteam/hardening/summary.md`, which `python3 redteam/hardening/rank.py` regenerates. "Before" values are copied from `REDTEAM.md` and were computed on the old three-experiment roster and weights, so before and after differ in scale.

## What was wrong and what changed

| Problem (REDTEAM) | Fix |
|---|---|
| All held-out answers were in the visible `data/*.jsonl`; the test reread labels and observations from those mutable files. | New held-out instances from **private seeds** that exist only in `eval/test/build_test_set.py`. Canonical observations and ground truth live only in `eval/test/instances/`. `data/*_test_inputs.jsonl` keeps observation fields only. The old public instances (labels already exposed) became the labeled training split. Test IDs start at 100000. |
| The test imported game/metric code from `data/`, which an agent can edit. | `eval/test/evaluate.py` is self-contained: numpy plus its own metric code. It imports nothing from `data/` or `method/`. `eval/train/` has its own independent copy. |
| No check of ID coverage or duplicates (a single row repeated 50 times passed). | Every held-out ID must be predicted exactly once. A missing or duplicate ID fails the experiment. |
| NaN/Inf/empty/null predictions crashed the scorer or produced NaN scores. | JSON `NaN`/`Infinity` are rejected. Shapes, finiteness and domain (budgets > 0, costs ≥ 0) are checked. Any invalid prediction scores that experiment as **failed**: recovery 0, every error metric at its cap of 1.0, every exploitability metric at its cap of 100. Per-instance errors and exploitabilities are clipped to the same caps, so no valid output scores below a failure. Scores are written with `allow_nan=False`. Unexpected exceptions also fail only that method. |
| The roster depended on `scores_train.json`, so Bertrand was silently dropped. 0.38 of the weight belonged to experiments the test never scored. | The roster is fixed in `eval/test/` and equals `scoring/reference.json`. Every method on disk is scored on every experiment; a missing experiment is scored as failed. Leontief, CD type+budget and Bertrand moved to `reference.json → unscored_paper_results`, with the paper numbers verbatim (reasons below). |
| The supplied simple baseline solved everything; the reference sat at the recovery bound everywhere (no headroom). | Added `fisher_cd_noisy_budget_recovery` (weight 0.4); see "Headroom check". |

## Variants: before and after

| Case | Before: test rank | After: test rank | After: train rank | Test recovery CD / linear / Cournot / noisy | Noisy mean rel. L2 |
|---|---:|---:|---:|---|---:|
| reference, seed 7 (shipped) | 0 | **0** | 0 | 1 / 1 / 1 / 0.605 | 0.0930 |
| reference, seed 8 | +2.6e-5 | +4.0e-5 | −0.0018 | 1 / 1 / 1 / 0.605 | 0.0930 |
| reference, seed 9 | +2.0e-5 | +0.0020 | +0.0021 | 1 / 1 / 1 / 0.610 | 0.0930 |
| stronger (4× iterations) | +0.000612 | +0.000498 | +0.00068 | 1 / 1 / 1 / 0.605 | 0.0931 |
| weaker (1 iteration) | −10.65 | **−18.57** | −18.77 | 0 / 0 / 0.12 / 0 | 0.938 |
| better: clearing-constrained noisy estimator (demo, reference elsewhere) | not run | **+0.165** | +0.142 | 1 / 1 / 1 / **0.910** | **0.044** |
| simple baseline: closed-form identities, noisy samples averaged (= `baseline/observed_expenditure.py` + Cournot first-order condition) | +0.000612 | **−0.136** | −0.133 | 1 / 1 / 1 / 0.340 | 0.127 |
| simple baseline, single noisy sample | not run | −1.050 | −0.856 | 1 / 1 / 1 / 0.035 | 0.373 |
| closed forms with log-averaged samples (honest alternative) | not run | −0.0089 | −0.011 | 1 / 1 / 1 / 0.585 | 0.095 |
| shipped `scripts/baseline.sh` (Fisher only, no Cournot predictions) | not run | −21.61 | −21.60 | 1 / 1 / failed / 0.340 | 0.127 |

Seed spread of the reference (max − min test rank over seeds 7/8/9): **0.0020**.

## Shortcuts: fix and score before and after

| Shortcut | Before | Fix | After (test) |
|---|---:|---|---:|
| label copy (read `budgets`/`marginal_cost` from visible data) | +0.000612 | Test labels are no longer in `data/`; held-out IDs come from a private seed. | **−107.11** (fails all four: no held-out predictions possible) |
| cherry-pick (repeat one good row for every row) | +0.000612 | Exact once-per-ID coverage check | **−107.11** (failed) |
| rewrite labels in `data/` to match the predictions | +0.000606 | Test reads only `eval/test/instances/` | **0** (identical to the reference it copies; the tampering has no effect) |
| replace fixed data with equilibria of constant guesses | +0.000612 | Same | **−10.87** (= the constant guess on the true data) |
| forged score file and flags | −16.58 | Already recomputed; still removed and recomputed | −10.87 |
| constant guesses | −16.58 | — | −10.87 |
| zero parameters | −72.21 | Zero budgets are out of domain → failed (a zero Cournot cost is valid and scored) | −94.48 |
| negative parameters | −105.77 | Out of domain → failed | −107.11 |
| empty / null parameters | no finite rank (scorer crashed) | Validated → failed | −107.11 |
| NaN / Infinity parameters | no finite rank (NaN scores) | Non-standard JSON rejected → failed | −107.11 |
| *new:* omit the hard experiment | — | Fixed roster; missing experiment → failed | −42.70 |
| *new:* one NaN row among valid rows | — | Any invalid row fails the experiment | −42.70 |
| *new:* predict only half of the test IDs | — | Coverage check | −107.11 |

−107.11 is the rank of a method that fails all four experiments. Train ranks show the intended asymmetry: label-copy and data-replacement inflate the *visible train* score (+0.235) but not the test.

## Shortcuts left, and why

- **Exact identities on the three exact-observation experiments.** Budget = observed expenditure p·xᵢ; Cournot cost from the first-order condition. These beat the reference by about 6e-4 in total, because they are exact to machine precision while the reference's iterative solver leaves about 1e-3 of residual error. This is an honest, genuinely more precise result, not a loophole. It cannot carry a method: the same idea on noisy samples loses (−0.136 with plain averaging, −0.009 with log averaging).
- **Visible training labels.** The train scorer reads `data/*_train.jsonl`, so copying or editing training labels inflates the *train* score. This is by design: the training split is public, and the hidden test is unaffected.
- **Known noise model and parameter range.** The briefing documents 16 samples and log-sd 0.3, and the training data show budgets in [0.1, 10]. Using this is legitimate prior knowledge; the reference already clips budgets to the parameter range.
- **Access to `eval/test/`.** The hidden ground truth is committed in `eval/test/instances/` (the designated location). An agent that can read that directory, or the git history that contains it, can read the answers. Protecting it is the hidden-test infrastructure's job.

## Reference score before and after

| Experiment (test split) | Before (old test: 50 odd IDs of the public files) | After (new hidden test) | After (train) |
|---|---|---|---|
| CD Fisher budgets: recovery / mean rel. L2 / avg. exploitability | 1.0 / 7.7e-4 / 6.2e-6 | 1.0 / 8.8e-4 / 7.8e-6 (n=100) | 1.0 / 7.7e-4 / 6.5e-6 |
| Linear Fisher budgets | 1.0 / 8.6e-4 / 7.5e-6 | 1.0 / 7.5e-4 / 5.7e-6 (n=100) | 1.0 / 8.1e-4 / 7.2e-6 |
| Cournot cost: recovery / mean rel. error / avg. exploitability | 1.0 / 3.2e-6 / 1.6e-10 | 1.0 / 3.3e-6 / 5.5e-10 (n=100) | 1.0 / 2.4e-6 / 2.6e-10 |
| CD Fisher budgets from noisy samples (new) | — | **0.605 / 0.0930 / 0.0238** (p90 0.143, max 0.188; n=200) | 0.615 / 0.0946 / 0.0252 |

The reproduced method is unchanged: same code paths, iterations, learning rates and seeds. Its noise-free results still match the paper's direction (paper: 100%/100%/95.2% recovery; 0.0004/0.0018/0.0000 exploitability). Train and test agree on every experiment. Its rank anchor is 0 by definition.

## Headroom check

- **At the bound:** `parameter_recovery_rate` = 1.0 for the reference on CD Fisher, linear Fisher and Cournot (both splits). Their error and exploitability metrics are at about 1e-3, 1e-5 and 1e-10; the total remaining gain on these three is about 6e-4. They are kept as reproduction and regression guards.
- **Added:** `fisher_cd_noisy_budget_recovery`. This targets where the paper's method falls short. The paper's inverse multiagent *learning* claim (Corollary 1, Sections 4–5: recovering parameters from sampled rather than exact equilibrium behavior) is never tested empirically in the paper. The reference (Algorithm 1 on the sample-average inverse-regret objective, same hyperparameters as the CD experiment) rationalizes the noisy samples as given and does not model the measurement noise. The posted prices are exact and the true equilibrium allocation is hidden, so no identity solves this experiment.
  - Simple baselines are clearly below the reference: averaged-sample expenditure reaches 0.340 recovery (rank −0.136), and the single-sample version 0.035 (−1.05).
  - There is clear room above the reference. A noise-aware estimate restricted to market-clearing budgets reaches 0.910 recovery and 0.044 mean relative L2 (+0.165). It lives in the audit runner only, not in `method/`, and is still not at the bound.
  - The metrics are not stuck: recovery spans 0.0 to 0.91 across the audited methods.
- **Weights:** noisy experiment 0.4; CD, linear and Cournot 0.2 each (previously 0.19 each, plus 0.19 Leontief, 0.19 CD type+budget, 0.05 Bertrand). The noisy experiment is the only one that can rank research progress, and it tests the paper's title claim (inverse multiagent *learning*), so it gets the largest weight. The weights still make failure on any exact-observation task (≥ 21 rank points) cost far more than the whole achievable noisy gain (≈ 0.24). A method that fails a task can therefore never outrank one that solves it through other metrics. Metric coefficients are unchanged.

## Removed from the scored roster (paper numbers kept verbatim in `unscored_paper_results`)

- **Bertrand cost recovery.** In the homogeneous-good duopoly the equilibrium price *is* the marginal cost, so the answer is part of the input. The reference sits exactly at every bound on both splits, cannot rank anything, and fails `validate.py` (primary metric identical on train and test).
- **Leontief budget recovery.** With an exact equilibrium, the budget equals the observed expenditure, so a one-line identity scores 100% while the reproduced nonsmooth Algorithm 1 reaches 21% (paper: 36.8%). A scored copy would reward the identity rather than research, and the earlier reproduction was rejected as too far from the paper.
- **CD type+budget recovery.** Exactly identified by spending shares, and never run successfully in this reproduction.

## Could not fix / limitations

- **Precision gains are now below seed noise.** The 4×-training variant's gain (+0.0005) is smaller than the reference seed spread (0.0020). One of the 200 noisy test markets sits at the 0.1 recovery threshold and flips between seeds, worth 0.4 × 1/200 = 0.002. Gains from optimizer precision alone therefore cannot be distinguished from seed luck. The shipped anchor uses fixed seeds (7/17), and method-level effects (paper method vs baselines: 0.136–18.6; better estimator: +0.165) are 70–9000 times larger. Making the reference converge fully would change the paper's 5000-iteration setting, so I left it.
- The three paper experiments that remain scored are saturated in this gym, because an exact observed equilibrium pins budgets and costs by identities. They measure reproduction, not research.
- The test assumes the ranker uses the formula above. `num_instances` has coefficient 0; coverage is enforced by the failure rule instead.

## Files

- Hidden test: `eval/test/evaluate.py`, `eval/test/build_test_set.py`, `eval/test/instances/*.jsonl`. Visible train scorer: `eval/train/evaluate.py`.
- Data: `data/*_train.jsonl` (labeled), `data/*_test_inputs.jsonl` (observations only), and the generator `data/fisher_markets.py::generate_cd_noisy_instances`.
- Method: `method/adversarial_inverse_fisher.py::run_sampled_algorithm_1`, plus multi-file `--instances` for all methods. Baseline: `baseline/observed_expenditure.py`.
- Scripts: `method.sh`, `reproduce.sh`, `evaluate*.sh`, `baseline.sh`, `download.sh`, `run.sh` (end-to-end reference reproduction plus validation).
- Audit: `redteam/hardening/runner.py` (CPU job, about 12 minutes), `redteam/hardening/rank.py`, `redteam/hardening/summary.{md,json}`, `redteam/hardening/cases/`.
