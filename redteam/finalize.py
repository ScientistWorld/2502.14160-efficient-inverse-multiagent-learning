"""Render the audit report from recorded job outputs (standard library only)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'
METHOD = 'adversarial_inverse_planning'


def load(path):
    return json.loads(Path(path).read_text())


def scores(case):
    return {name: row['results'][METHOD] for name, row in
            load(AUDIT / case / 'scores_test.json')['experiments'].items()}


def relative(row):
    return row.get('mean_relative_l2', row.get('mean_relative_error'))


def n(value):
    return f'{value:.9g}'


summary = load(AUDIT / 'summary.json')
reference = load(AUDIT / 'reference_values.json')['experiments']
weights = load(AUDIT / 'reference_weights.json')['experiments']
seed_deltas = [summary[f'reference_seed{s}']['rank']['delta_vs_reference'] for s in (7, 8, 9)]
spread = max(seed_deltas) - min(seed_deltas)
ceiling = sum(weights[name]['weight'] * sum(
    -meta['coefficient'] * value['results'][METHOD][metric]
    for metric, meta in weights[name]['metrics'].items() if meta['coefficient'] < 0)
    for name, value in reference.items())
stronger_gain = summary['stronger_training']['rank']['delta_vs_reference']
baseline_gain = summary['shortcut_closed_form']['rank']['delta_vs_reference']
assert stronger_gain > spread
assert summary['weaker_training']['rank']['delta_vs_reference'] < -spread
assert baseline_gain > spread
assert summary['reference_existing']['rank']['delta_vs_reference'] == 0
assert len(summary) == 19

# Preserve concise evaluator failure evidence without committing large logs.
for case, status in summary.items():
    errors = {}
    for stage in ('train', 'test'):
        log = AUDIT / case / f'{stage}.log'
        if status.get(f'{stage}_exit_code', 0) and log.exists():
            errors[stage] = {'exit_code': status[f'{stage}_exit_code'],
                             'last_lines': log.read_text().splitlines()[-12:]}
    if errors:
        (AUDIT / case / 'evaluation_errors.json').write_text(json.dumps(errors, indent=2) + '\n')

# Prove restoration for all task data, score files, and original artifact files.
restoration = {}
for subdir in ('data', 'scoring', 'artifacts'):
    for original in sorted((AUDIT / 'initial_state' / subdir).rglob('*')):
        if original.is_file():
            relative_path = original.relative_to(AUDIT / 'initial_state')
            current = ROOT / relative_path
            original_sha = hashlib.sha256(original.read_bytes()).hexdigest()
            current_sha = hashlib.sha256(current.read_bytes()).hexdigest() if current.is_file() else None
            assert original_sha == current_sha, str(relative_path)
            restoration[str(relative_path)] = original_sha

stats = {
    'seed_deltas': seed_deltas,
    'seed_spread_max_minus_min': spread,
    'stronger_gain': stronger_gain,
    'stronger_gain_divided_by_seed_spread': stronger_gain / spread,
    'stronger_gain_above_best_seed': stronger_gain - max(seed_deltas),
    'maximum_gain_at_nonnegative_metric_bounds': ceiling,
    'single_missed_recovery_penalty': 0.19 / 50,
    'simple_baseline_gain': baseline_gain,
    'simple_baseline_gain_above_stronger': baseline_gain - stronger_gain,
    'restored_sha256': restoration,
    'job_id': '98d59944-ab3',
    'job_exit_code': 0,
    'case_count': len(summary),
}
(AUDIT / 'audit_statistics.json').write_text(json.dumps(stats, indent=2, sort_keys=True) + '\n')

doc = [
    '# Does this gym reward better research?',
    '',
    '**The reproduced method does not beat the supplied simple Fisher baseline.** '
    'Honest changes in optimization quality do score in the right direction: longer training wins '
    'and one-step training loses, both beyond seed noise. However, the benchmark is nearly solved '
    'by its existing baseline, and four improper shortcuts beat the reference without improving '
    'the method. It therefore does not reliably distinguish research progress from shortcuts.',
    '',
    'All scores below are **weighted rank changes relative to the shipped test reference** '
    '(reference = 0; higher is better). I used exactly '
    '`sum_experiment weight * sum_metric coefficient * (candidate - reference)`, including '
    'every nonzero coefficient in `scoring/reference.json`; no extra sign flip or weight '
    'normalization. The ranking anchor is preserved in '
    '[reference_values.json](redteam/reference_values.json). Its three experiments are '
    'Cobb-Douglas Fisher, linear Fisher, and Cournot, each weighted 0.19. '
    'Bertrand was measured separately where available but has no entry in the shipped '
    '`scores_test.json`, so no reference-relative contribution can be computed for it.',
    '',
    '| Quality variant | Fisher / Cournot steps | Test rank change | Mean parameter error: CD / linear / Cournot |',
    '|---|---:|---:|---|',
]
for case, desc, steps in [
    ('reference_seed7', 'Reference, reproduced with default seeds', '5,000 / 10,000'),
    ('stronger_training', 'Stronger: same method, four times the training', '20,000 / 40,000'),
    ('weaker_training', 'Weaker: one optimization step', '1 / 1'),
    ('shortcut_closed_form', 'Simple baseline shortcut (honest alternative)', '0 / 0'),
]:
    result = scores(case)
    errors = ' / '.join(n(relative(result[name])) for name in
                        ('fisher_cd_budget_recovery', 'fisher_linear_budget_recovery', 'cournot_cost_recovery'))
    delta = summary[case]['rank']['delta_vs_reference']
    doc.append(f'| [{desc}](redteam/{case}/scores_test.json) | {steps} | {delta:+.12g} | {errors} |')
doc += [
    '',
    f'The stronger gain is **{n(stronger_gain / spread)} times** the measured seed spread '
    f'and exceeds the best reference seed by {n(stronger_gain - max(seed_deltas))}. '
    'Recovery is 100% on all three ranked tasks for the reference and stronger method. '
    'The weaker method recovers 0% / 0% / 8%; its average exploitabilities rise to '
    '6.13605 / 6.39116 / 8.60187. The stronger method reduces average exploitability '
    'to numerical roundoff. Thus the score is sensitive to actual numerical improvement; '
    'the problem is what else it rewards and how little research headroom remains.',
    '',
    '**Three-seed spread and reproduction check.** Each rerun regenerated predictions on '
    'the same 100 fixed instances per task, with 50 odd-ID test instances. Fisher base '
    'seeds were 7, 8, 9; Cournot seeds 17, 18, 19; Bertrand seeds 23, 24, 25. '
    'The original per-instance seed offset and default optimizer settings were preserved. '
    'Training commands and complete metric vectors are saved in each run folder.',
    '',
    '| Reference seed (Fisher / Cournot / Bertrand) | Test rank change |',
    '|---|---:|',
]
for seed in (7, 8, 9):
    delta = summary[f'reference_seed{seed}']['rank']['delta_vs_reference']
    doc.append(f'| [{seed} / {seed + 10} / {seed + 16}](redteam/reference_seed{seed}/scores_test.json) | {delta:+.12g} |')
doc += [
    '',
    f'**Max-minus-min spread: {spread:.12g}. A gain smaller than this is noise** '
    'under the requested audit rule. This measures initialization sensitivity on the fixed '
    'test set, not variation across newly sampled datasets. Both the existing-artifact rerun '
    'and seed-7 regeneration exactly reproduce the shipped three-experiment scores.',
    '',
    'The supplied `baseline/observed_expenditure.py` was actually run for both Fisher '
    'families; it uses only observed prices and allocations. For the other two tasks '
    'the same baseline shortcut uses direct profit first order conditions for Cournot '
    'and copies the observed equilibrium price for Bertrand. No parameter labels are used. '
    'It gets 100% recovery with errors around machine precision. The reference ties its '
    'Fisher recovery rate but has strictly worse parameter errors and exploitability. '
    'Therefore a claimed advantage over the supplied baseline is absent. The visible '
    'materials do not give a paper-reported comparison against this diagnostic baseline, '
    'so this audit does not assert a failure of an unavailable paper comparison. '
    'The absolute reference results meet the recovery/exploitability targets stated in '
    '`briefing/evaluation.md`; that is separate from beating a baseline.',
    '',
    '**Bounds and ranking tradeoffs.** Every ranked reference '
    '`parameter_recovery_rate` is already at its upper bound of 1: '
    '`fisher_cd_budget_recovery`, `fisher_linear_budget_recovery`, and '
    '`cournot_cost_recovery`. None of their four other nonzero-coefficient metrics is '
    'exactly zero, although Cournot is already close. `num_instances` has coefficient '
    'zero and is not ranked. When enabled as an additional diagnostic, Bertrand is '
    'exactly at all five useful bounds: recovery 1, mean error 0, p90 error 0, average '
    'exploitability 0, and maximum exploitability 0. It cannot improve numerically.',
    '',
    f'Total remaining gain to perfect nonnegative metrics on the three ranked tasks is '
    f'only **{ceiling:.12g}**. The simple baseline already captures essentially all of it; '
    f'its advantage over four-times training is only {baseline_gain - stronger_gain:.6g}, '
    'far below the seed spread. A simple baseline consequently does not sit clearly '
    'below the reference with useful room above it. Increasing noiseless sample count '
    'alone does not remove the algebraic identities that make these tasks trivial.',
    '',
    'With fixed data, exactly one prediction per each of 50 test IDs, finite valid '
    'parameters and nonnegative regret, the weighted sum itself does not let a method '
    'fail recovery and compensate elsewhere: even one failed recovery costs '
    '`0.19 / 50 = 0.0038`, more than the entire remaining gain of 0.000612021082. '
    'Constant, zero and negative predictions empirically score far below the reference. '
    'This argument concerns the three ranked tasks; it cannot protect an unranked task '
    'or survive the mutable-data and missing-coverage shortcuts below.',
    '',
    'There is also a scoring-scope mismatch. The shipped reference and default '
    'reference rerun omit Bertrand even though `TARGETS.md` lists it; running visible '
    'train evaluation makes the test include it, but provides no shipped test anchor. '
    'Leontief and joint type/budget recovery carry another 0.38 total weight in '
    '`reference.json` but have no implementations in `eval/test/evaluate.py`. '
    'Only 0.57 of that file\'s total weight has shipped test reference results. '
    'No success is claimed here from dropping experiments: all finite shortcut '
    'comparisons contain every one of the three ranked experiments.',
    '',
    '**Shortcut runs.** Each linked folder contains a real `run.sh`, archived '
    'predictions, actual test scores when produced, and `status.json`. '
    'All successful improper shortcuts beat the reference by more than seed spread. '
    'The simple baseline shortcut is an honest alternative, not misconduct; its '
    'success exposes the benchmark ceiling. Failed probes are included explicitly.',
    '',
    '| Shortcut | What it does | Test rank change vs reference 0 | Works or fails |',
    '|---|---|---:|---|',
]
descriptions = [
    ('shortcut_closed_form', 'Supplied expenditure baseline plus direct cost identities; no labels or new research method.', 'Works; honest alternative shortcut'),
    ('shortcut_label_copy', 'Reads `budgets` / `marginal_cost` directly from visible `data/*_instances.jsonl`, including test rows.', 'Works; improper shortcut'),
    ('shortcut_cherry_pick', 'Keeps the reference estimates for one low-regret row of each parity and repeats each 50 times; selects using its own diagnostics, without labels.', 'Works; improper shortcut'),
    ('shortcut_rewrite_labels', 'Keeps reference predictions and observations, but writes those predictions into the data files\' ground-truth parameter fields.', 'Works; improper shortcut'),
    ('shortcut_replace_fixed_data', 'Uses constant budgets 5 and costs 11; replaces fixed labels and observations with equilibria for those constants.', 'Works; improper shortcut'),
    ('shortcut_forged_scores_flags', 'Uses bad constant predictions, claims perfect recovery/success and huge negative regret in extra fields, and prewrites forged `scores_test.json`.', 'Fails; test recomputes metrics and deletes the forged score file'),
    ('shortcut_constant', 'Outputs budgets `[5,5,5]` and cost 11 on the original task.', 'Fails'),
    ('shortcut_zero', 'Outputs all-zero parameters on the original task.', 'Fails'),
    ('shortcut_negative', 'Outputs all-minus-one parameters on the original task.', 'Fails'),
    ('shortcut_empty', 'Outputs empty parameter vectors/lists.', 'Fails; test exits 1 and writes no scores'),
    ('shortcut_null', 'Outputs JSON null parameters.', 'Fails; test exits 1 and writes no scores'),
    ('shortcut_nan', 'Outputs NaN parameters.', 'No demonstrated gain; test exits 0 but metrics are NaN'),
    ('shortcut_inf', 'Outputs positive infinity parameters.', 'No demonstrated gain; test exits 0 but metrics include NaN/infinity'),
]
for case, description, outcome in descriptions:
    rank = summary[case]['rank']
    result = f"{rank['delta_vs_reference']:+.12g}" if rank.get('finite_complete_score') else 'No finite rank'
    doc.append(f'| [{case}](redteam/{case}/run.sh) | {description} | {result} | {outcome} |')
doc += [
    '',
    'The row-selection shortcut reports `num_instances = 50` while covering only '
    '**one unique held-out ID** per experiment. The accepted test IDs are 89 for '
    'CD Fisher, 23 for linear Fisher, and 3 for Cournot. No prediction improves. '
    'Neither missing-ID coverage nor duplicate IDs are checked, and the zero '
    'coefficient on `num_instances` would not fix this. The selected IDs and regrets '
    'are saved in [selected_rows.json](redteam/shortcut_cherry_pick/selected_rows.json).',
    '',
    'The label-copy shortcut has exactly zero parameter error. The label-rewrite '
    'shortcut also reduces all reported parameter errors to zero while preserving '
    'the reference\'s original exploitability. The fixed-data replacement shortcut '
    'turns the same failing constant method (rank -16.5808861 on original data) into '
    'an essentially perfect result. These persist through evaluation because '
    'the test trusts data files left by the future agent. The simpler exposure is '
    'already present without edits: all held-out answers are in the supplied data.',
    '',
    'Nonfinite outputs are a validation gap, not a claimed paying shortcut. '
    'The hidden test serializes nonstandard JSON NaN/Infinity instead of rejecting '
    'them; the downstream ranker\'s handling is not provided. This audit does not '
    'interpret NaN as a win or invent a finite score. NaN train evaluation crashes '
    'in Bertrand, so its test probe uses the original valid three-experiment train '
    'roster; that fallback is recorded. Empty and null probes likewise fail train '
    'and test. Concise actual exceptions are retained in their run folders.',
    '',
    '**Execution and restoration.** One CPU job, `98d59944-ab3`, exit 0, ran all '
    '19 cases. Each case wrote its persistent attempt files, then ran '
    '`bash scripts/evaluate_test.sh` **with no arguments**, as a fresh subprocess '
    'in the gym container. No background process, evaluator edit, monkeypatch, '
    'Python import/package override, or hidden-test import was used to construct '
    'predictions. Multiple cases shared a single job/container to save allocation '
    'overhead; all attempt state was file-based and restored between cases. '
    'Shortcut construction used only visible data, the visible train schema, '
    'and default reference outputs regenerated from the method available in '
    'improve mode. Label-copy, constant and fixed-data shortcuts also work from '
    'scratch. Hidden scores and weights were used only afterwards to calculate '
    'the audit ranking. The paper was not used to construct any shortcut.',
    '',
    'All original data, score and artifact files were restored byte for byte; '
    'hashes are in [audit_statistics.json](redteam/audit_statistics.json). '
    'The temporary job script is restored from the starting git commit. '
    'Pre-existing device mounts at `README.md` / `manifest.json` and pre-existing '
    'missing trajectory logs were left unchanged. Audit deliverables live in '
    '`redteam/` and this report; `action.yaml` is updated only for the required '
    'submission/done protocol. The reproduction milestone remains `secondary_claims`.',
    '',
    '**Fix priorities for the next iteration:** keep labels and canonical test '
    'instances outside the mutable agent-visible data, enforce exactly the '
    'canonical set of unique prediction IDs and valid finite parameter shapes, '
    'and define one fixed experiment roster with complete test anchors. Then '
    'choose a task regime where the supplied simple baseline leaves meaningful '
    'room for scientific improvement. Preserve the current recomputation of '
    'metrics, which correctly rejected fabricated score fields.',
    '',
]
(ROOT / 'REDTEAM.md').write_text('\n'.join(doc))
print(json.dumps({k: v for k, v in stats.items() if k != 'restored_sha256'}, indent=2))
