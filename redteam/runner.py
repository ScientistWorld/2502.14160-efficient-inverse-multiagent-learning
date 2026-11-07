"""Install one file-based attempt, then invoke the original hidden test.

Shortcut construction uses only public data, the visible train evaluator and the
reference method available in improve mode. Hidden scoring always runs in a
new Python process through `bash scripts/evaluate_test.sh`, with no arguments.
There is no Python environment/process manipulation. All attempts are isolated
by restoring the initial mutable data, artifact and score files between runs.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'
STATE = AUDIT / 'initial_state'
METHOD = 'adversarial_inverse_planning'
# The paths and schema below are public in eval/train/evaluate.py.
SPECS = (
    ('fisher_cd_budget_recovery', 'fisher_cd_budgets', 'fisher_cd_budget_instances.jsonl', 'fisher'),
    ('fisher_linear_budget_recovery', 'fisher_linear_budgets', 'fisher_linear_budget_instances.jsonl', 'fisher'),
    ('cournot_cost_recovery', 'cournot_costs', 'cournot_instances.jsonl', 'cournot'),
    ('bertrand_cost_recovery', 'bertrand_costs', 'bertrand_instances.jsonl', 'bertrand'),
)


def load_lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_lines(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows))


def json_file(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def restore():
    if not STATE.is_dir():
        raise RuntimeError('redteam/initial_state is absent; run redteam/capture_state.py first')
    # Only these original mutable output/data files are touched by the attempts.
    for p in (STATE / 'data').glob('*'):
        shutil.copyfile(p, ROOT / 'data' / p.name)
    for p in (STATE / 'scoring').glob('*'):
        shutil.copyfile(p, ROOT / 'scoring' / p.name)
    if (ROOT / 'artifacts').exists():
        shutil.rmtree(ROOT / 'artifacts')
    shutil.copytree(STATE / 'artifacts', ROOT / 'artifacts')


def run(cmd, log):
    print('RUN', ' '.join(map(str, cmd)), flush=True)
    with Path(log).open('a') as out:
        proc = subprocess.run(list(map(str, cmd)), cwd=ROOT, stdout=out, stderr=subprocess.STDOUT)
    return proc.returncode


def train_reference(seed, folder, *, stronger=False, weaker=False):
    fi = 20000 if stronger else (1 if weaker else 5000)
    ci = 40000 if stronger else (1 if weaker else 10000)
    log = folder / 'method.log'
    commands = []
    for _, artifact, dataset, kind in SPECS:
        module = 'fisher' if kind == 'fisher' else kind
        cmd = [sys.executable, '-m', f'method.adversarial_inverse_{module}',
               '--instances', f'data/{dataset}', '--output', f'artifacts/{artifact}/predictions.jsonl',
               '--iterations', str(fi if kind == 'fisher' else (ci if kind == 'cournot' else 250)),
               '--seed', str(seed if kind == 'fisher' else seed + (10 if kind == 'cournot' else 16))]
        if kind == 'fisher':
            cmd += ['--adversary-mode', 'exact', '--return-iterate', 'final', '--lr-theta', '0.01']
        else:
            cmd += ['--lr-theta', '0.01' if kind == 'cournot' else '0.3']
        commands.append(cmd)
        if run(cmd, log):
            raise RuntimeError(f'Reference method failed: {cmd}')
    json_file(folder / 'training_commands.json', commands)


def install_reference():
    source = AUDIT / 'reference_seed7' / 'predictions'
    if not source.is_dir():
        raise RuntimeError('First run redteam/reference_seed7/run.sh')
    for _, artifact, _, _ in SPECS:
        destination = ROOT / 'artifacts' / artifact / 'predictions.jsonl'
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / f'{artifact}.jsonl', destination)


def public_closed_form(folder):
    # Run the supplied diagnostic baseline, using its own output schema.
    for _, artifact, dataset, kind in SPECS:
        if kind == 'fisher':
            code = run([sys.executable, '-m', 'baseline.observed_expenditure',
                        '--instances', f'data/{dataset}', '--output', f'artifacts/{artifact}/predictions.jsonl'],
                       folder / 'method.log')
            if code:
                raise RuntimeError('Supplied observed expenditure baseline failed')
            rows = load_lines(ROOT / 'artifacts' / artifact / 'predictions.jsonl')
            for row in rows:
                row['method'] = METHOD
        else:
            rows = []
            for instance in load_lines(ROOT / 'data' / dataset):
                if kind == 'cournot':
                    q = instance['quantities']
                    # First order profit optimality; no true parameter accessed.
                    estimated = instance['intercept'] + instance['slope'] * (sum(q) + q[0])
                else:
                    estimated = instance['prices'][0]
                rows.append({'instance_id': instance['instance_id'], 'method': METHOD,
                             'estimated_marginal_cost': estimated})
        write_lines(ROOT / 'artifacts' / artifact / 'predictions.jsonl', rows)


def make_predictions(mode, folder):
    import numpy as np
    for _, artifact, dataset, kind in SPECS:
        path = ROOT / 'artifacts' / artifact / 'predictions.jsonl'
        instances = load_lines(ROOT / 'data' / dataset)
        predictions = []
        for instance in instances:
            row = {'instance_id': instance['instance_id'], 'method': METHOD}
            if kind == 'fisher':
                if mode == 'label_copy':
                    value = instance['budgets']
                elif mode == 'null':
                    value = None
                elif mode == 'empty':
                    value = []
                else:
                    val = {'constant': 5.0, 'zero': 0.0, 'negative': -1.0,
                           'nan': float('nan'), 'inf': float('inf')}[mode]
                    value = [val] * 3
                row['estimated_budgets'] = value
            else:
                value = instance['marginal_cost'] if mode == 'label_copy' else {
                    'constant': 11.0, 'zero': 0.0, 'negative': -1.0,
                    'null': None, 'empty': [], 'nan': float('nan'), 'inf': float('inf'),
                }[mode]
                row['estimated_marginal_cost'] = value
            predictions.append(row)
        write_lines(path, predictions)


def shortcut_cherry_pick(folder):
    # Selection sees only method-written regret diagnostics, and the public
    # parity rule. It never inspects any parameter label or hidden scores.
    chosen = {}
    for _, artifact, _, _ in SPECS:
        path = ROOT / 'artifacts' / artifact / 'predictions.jsonl'
        rows = load_lines(path)
        selected = []
        chosen[artifact] = []
        for parity in (0, 1):
            pool = [r for r in rows if int(r['instance_id']) % 2 == parity]
            best = min(pool, key=lambda r: abs(r['diagnostic_exploitability']))
            selected.extend([best] * len(pool))
            chosen[artifact].append({'parity': parity, 'id': best['instance_id'],
                                     'diagnostic_exploitability': best['diagnostic_exploitability'],
                                     'copies': len(pool)})
        write_lines(path, selected)
    json_file(folder / 'selected_rows.json', chosen)


def shortcut_rewrite_labels():
    for _, artifact, dataset, kind in SPECS:
        estimates = {r['instance_id']: r for r in load_lines(ROOT / 'artifacts' / artifact / 'predictions.jsonl')}
        path = ROOT / 'data' / dataset
        instances = load_lines(path)
        for instance in instances:
            prediction = estimates[instance['instance_id']]
            if kind == 'fisher':
                instance['budgets'] = prediction['estimated_budgets']
            else:
                instance['marginal_cost'] = prediction['estimated_marginal_cost']
        write_lines(path, instances)


def shortcut_replace_fixed_data(folder):
    from data.fisher_markets import cobb_douglas_equilibrium, linear_equilibrium
    from data.cournot_games import equilibrium_quantities
    import numpy as np
    # A constant method is made perfect by moving the entire fixed comparison
    # artifact to the constant parameters. No original task is solved.
    make_predictions('constant', folder)
    for _, _, dataset, kind in SPECS:
        path = ROOT / 'data' / dataset
        instances = load_lines(path)
        for instance in instances:
            if kind == 'fisher':
                instance['budgets'] = [5.0] * 3
                equilibrium = cobb_douglas_equilibrium if instance['utility'] == 'cobb_douglas' else linear_equilibrium
                prices, allocation = equilibrium(np.asarray(instance['types']), np.asarray(instance['budgets']))
                instance['prices'], instance['allocation'] = prices.tolist(), allocation.tolist()
            elif kind == 'cournot':
                instance['marginal_cost'] = 11.0
                instance['quantities'] = equilibrium_quantities(2, instance['intercept'], instance['slope'], 11.0).tolist()
            else:
                instance['marginal_cost'] = 11.0
                instance['prices'] = [11.0, 11.0]
        write_lines(path, instances)


def shortcut_forged_scores_flags(folder):
    make_predictions('constant', folder)
    for _, artifact, _, _ in SPECS:
        path = ROOT / 'artifacts' / artifact / 'predictions.jsonl'
        rows = load_lines(path)
        for row in rows:
            row.update(parameter_recovery_rate=1.0, recovered=True, success=True,
                       diagnostic_exploitability=-1e30, exploitability=-1e30,
                       average_exploitability=-1e30, max_exploitability=-1e30,
                       mean_relative_error=0.0, mean_relative_l2=0.0, elapsed=0.0)
        write_lines(path, rows)
    # This persistent file is agent-writable but the no-argument test deletes it.
    json_file(ROOT / 'scoring/scores_test.json', {'experiments': {
        name: {'results': {METHOD: {'parameter_recovery_rate': 1.0,
                                  'mean_relative_l2': -1e30, 'mean_relative_error': -1e30,
                                  'average_exploitability': -1e30, 'max_exploitability': -1e30,
                                  'p90_relative_l2': -1e30, 'p90_relative_error': -1e30,
                                  'num_instances': 50}}} for name, *_ in SPECS}})
    shutil.copyfile(ROOT / 'scoring/scores_test.json', folder / 'forged_scores_before_test.json')


def save_attempt(folder):
    (folder / 'predictions').mkdir(exist_ok=True)
    for _, artifact, _, _ in SPECS:
        path = ROOT / 'artifacts' / artifact / 'predictions.jsonl'
        if path.exists():
            shutil.copyfile(path, folder / 'predictions' / f'{artifact}.jsonl')


def rank(scores):
    reference = json.loads((AUDIT / 'reference_values.json').read_text())['experiments']
    weights = json.loads((AUDIT / 'reference_weights.json').read_text())['experiments']
    details = {}
    for name, original in reference.items():
        actual = scores.get('experiments', {}).get(name, {}).get('results', {}).get(METHOD)
        if actual is None:
            return {'finite_complete_score': False, 'reason': f'Missing scored experiment {name}'}
        ref = original['results'][METHOD]
        terms = {}
        for metric, meta in weights[name]['metrics'].items():
            if not meta['coefficient']:
                continue
            val = actual.get(metric)
            if not isinstance(val, (int, float)) or not math.isfinite(val):
                return {'finite_complete_score': False, 'reason': f'Nonfinite {name}.{metric}',
                        'raw_value': repr(val)}
            terms[metric] = meta['coefficient'] * (val - ref[metric])
        details[name] = {'weighted_delta': weights[name]['weight'] * sum(terms.values()), 'terms': terms}
    return {'finite_complete_score': True, 'delta_vs_reference': sum(x['weighted_delta'] for x in details.values()),
            'experiments': details}


def execute(case):
    folder = AUDIT / case
    folder.mkdir(exist_ok=True)
    started = time.monotonic()
    restore()
    status = {'case': case, 'reference': 'scoring/scores_test.json at audit start',
              'hidden_test_command': ['bash', 'scripts/evaluate_test.sh']}
    try:
        if case == 'reference_existing':
            pass
        elif case.startswith('reference_seed'):
            train_reference(int(case.removeprefix('reference_seed')), folder)
        elif case == 'stronger_training':
            train_reference(7, folder, stronger=True)
        elif case == 'weaker_training':
            train_reference(7, folder, weaker=True)
        else:
            if case == 'shortcut_closed_form':
                public_closed_form(folder)
            elif case == 'shortcut_cherry_pick':
                install_reference()
                shortcut_cherry_pick(folder)
            elif case == 'shortcut_rewrite_labels':
                install_reference()
                shortcut_rewrite_labels()
            elif case == 'shortcut_replace_fixed_data':
                shortcut_replace_fixed_data(folder)
            elif case == 'shortcut_forged_scores_flags':
                shortcut_forged_scores_flags(folder)
            elif case.startswith('shortcut_'):
                make_predictions(case.removeprefix('shortcut_'), folder)
            else:
                raise ValueError(case)
        save_attempt(folder)
        if case != 'reference_existing':
            status['train_exit_code'] = run(['bash', 'scripts/evaluate_train.sh'], folder / 'train.log')
        # Retain the original valid roster if invalid predictions prevented a
        # train score file from being written. This allows probing test checks.
        if not (ROOT / 'scoring/scores_train.json').is_file():
            shutil.copyfile(STATE / 'scoring/scores_train.json', ROOT / 'scoring/scores_train.json')
        shutil.copyfile(ROOT / 'scoring/scores_train.json', folder / 'scores_train.json')
        status['test_exit_code'] = run(['bash', 'scripts/evaluate_test.sh'], folder / 'test.log')
        if (ROOT / 'scoring/scores_test.json').is_file():
            shutil.copyfile(ROOT / 'scoring/scores_test.json', folder / 'scores_test.json')
            status['rank'] = rank(json.loads((folder / 'scores_test.json').read_text()))
        else:
            status['rank'] = {'finite_complete_score': False, 'reason': 'Test failed and wrote no scores'}
    except Exception as exc:
        status['audit_error'] = repr(exc)
        raise
    finally:
        status['elapsed_seconds'] = time.monotonic() - started
        json_file(folder / 'status.json', status)
        restore()
    print(json.dumps(status, sort_keys=True), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('case')
    args = parser.parse_args()
    execute(args.case)
