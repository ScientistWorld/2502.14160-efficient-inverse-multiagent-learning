"""Capture mutable files before the audit; standard library only."""
from pathlib import Path
import json
import shutil
import subprocess

root = Path('/home/user')
audit = root / 'redteam'
dst = audit / 'initial_state'
if dst.exists():
    raise SystemExit('Initial state already captured; refusing to overwrite it')
dst.mkdir(parents=True)
paths = [*root.glob('data/*_instances.jsonl'), *root.glob('scoring/scores*.json'),
         root / 'scripts/run.sh', root / 'action.yaml']
for p in paths:
    q = dst / p.relative_to(root)
    q.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, q)
shutil.copytree(root / 'artifacts', dst / 'artifacts')
for src, target in [('scoring/scores_test.json', 'reference_values.json'),
                    ('scoring/reference.json', 'reference_weights.json')]:
    # Never replace the audit's original ranking anchor on reruns.
    if not (audit / target).exists():
        shutil.copyfile(root / src, audit / target)
(audit / 'start.json').write_text(json.dumps({
    'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'preexisting_status': subprocess.check_output(['git', 'status', '--short'], text=True),
    'note': 'README.md and manifest.json are pre-existing /dev/null device mounts; trajectory deletions also predate the audit. These are preserved.',
}, indent=2) + '\n')
