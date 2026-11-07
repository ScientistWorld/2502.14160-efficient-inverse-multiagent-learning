# Audit runs

Run `python3 redteam/capture_state.py` once before using these runners. Submit
`bash redteam/bundle.sh` as a CPU job in the original gym container. Each case
also has its own `run.sh`. The cherry-pick and label-rewrite shortcuts reuse
the outputs of `redteam/reference_seed7/run.sh`, which is the original method
with its default seed and training configuration. Other shortcuts construct
their predictions directly from the visible inputs. The initial reference's three scored
experiments define the ranking comparison; the fourth experiment, Bertrand,
is measured as an additional diagnostic when train evaluation enables it.

Each runner restores original mutable data and artifacts, installs its method
or shortcut, executes visible train evaluation, invokes
`bash scripts/evaluate_test.sh` with no arguments in a separate process, and
archives predictions, train/test scores and status in its own folder. Hidden
evaluation code and Python environments are never modified. Only persistent
files carry the attempts into evaluation. Each attempt restores the original
files on exit. Scores for nonfinite outputs are retained verbatim and are not
called successful rankings.

`reference_values.json` and `reference_weights.json` preserve the original
ranking anchor. `initial_state/` is a local, ignored restoration cache.
`summary.json` records actual ranking deltas and coverage. `job_metadata.json`
preserves the completed CPU job's status and timing. Logs are ignored.

The closed form **shortcut** is an honest alternative: the supplied Fisher
baseline and direct profit first order conditions solve these noiseless
instances without a new research method. It is labeled a shortcut to distinguish
that benchmark limitation from scientific progress. It does not read labels.
