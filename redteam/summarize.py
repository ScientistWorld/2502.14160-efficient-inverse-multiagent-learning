"""Collect the measured ranking deltas and independent coverage diagnostics."""
import json
from pathlib import Path
from redteam.runner import AUDIT, METHOD, SPECS, load_lines, json_file

cases = {}
for path in sorted(AUDIT.glob('*/status.json')):
    status = json.loads(path.read_text())
    coverage = {}
    for name, artifact, _, _ in SPECS:
        prediction = path.parent / 'predictions' / f'{artifact}.jsonl'
        if prediction.exists():
            rows = load_lines(prediction)
            test = [row for row in rows if row['instance_id'] % 2]
            coverage[name] = {'test_rows': len(test), 'unique_test_ids': len({r['instance_id'] for r in test})}
    status['coverage'] = coverage
    cases[path.parent.name] = status
json_file(AUDIT / 'summary.json', cases)
for name, status in cases.items():
    print(name, status.get('rank'), flush=True)
