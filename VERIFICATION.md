# Verification Report

> **Superseded (hardening iteration, 2026-11-07):** the scored roster, data layout and evaluators changed; see `HARDENING.md`. The notes below describe the earlier gym.

## Initial Assessment

The workspace entered final verification at `secondary_claims`. The milestone is justified by four accepted scored static experiments: Cobb-Douglas Fisher budget recovery, linear Fisher budget recovery, Cournot marginal-cost recovery, and Bertrand marginal-cost recovery. The Leontief setting is documented as unreproduced because its corrected result was too far from the paper report. A newer Cobb-Douglas type-and-budget implementation was present, but no completed job had produced accepted scores for it.

## Issues Found

- Minor: method-agnostic target and experiment docs listed the unscored Cobb-Douglas type-and-budget setting even though it was absent from `scoring/scores.json`.
- Minor: default `scripts/method.sh`, `scripts/reproduce.sh`, and train/test discovery included the unverified type-and-budget path, which could make a fresh default run diverge from the accepted scored suite.
- Cosmetic: generated Python cache directories were present under workspace code folders.
- Cosmetic: stale tracked `trajectory/` run logs had already been deleted and needed to be committed so the repository is clean.

## Fixes Applied

- Narrowed `briefing/problem.md`, `briefing/evaluation.md`, `scoring/EXPERIMENTS.md`, `scoring/TARGETS.md`, `scoring/CONSTRAINTS.md`, and `scoring/DIRECTION.md` to the accepted scored suite.
- Removed the unverified type-and-budget setting from default method/reproduce/evaluate discovery while leaving the implementation and explicit evaluator selector available as an unscored extension.
- Updated `PROGRESS.md`, `MILESTONES.md`, and `scripts/run.sh` to reflect the final accepted suite.
- Removed generated Python cache directories from workspace-owned code paths.
- Ran `python validate.py --compare`, shell syntax checks, `git diff --check`, and a consistency check that `scoring/EXPERIMENTS.md` matches `scoring/scores.json`.

## Final Judgment

The workspace is ready to serve as a gym for the accepted static inverse-game experiments. Problem/solution separation is clean: `eval/` and `data/` do not import from `method/`, public problem/evaluation docs describe the task and metrics rather than the paper algorithm, and scoring reads prediction artifacts rather than rerunning the method. The scoring surface includes both parameter-recovery benefit metrics and exploitability/error constraint metrics.

- Milestone: secondary_claims
- Ready for gym use: yes
- Confidence: medium
- Key limitation: the gym covers a validated static subset; Leontief and Cobb-Douglas type-plus-budget remain unscored extension targets.
