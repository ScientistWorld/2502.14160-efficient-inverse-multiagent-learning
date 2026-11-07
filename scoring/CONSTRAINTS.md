# Constraints

For comparable scores, keep the benchmark instances fixed: do not regenerate, edit or replace the files in `data/` that a run is scored against. The hidden test split uses its own canonical copy of the test instances and ignores any change to `data/`.

- **Fisher experiments**: 3 buyers, 2 unit-supply goods, known utility types (Cobb-Douglas or linear), unknown budgets. Output one recovered budget vector per instance from the provided observations only: prices and allocations for the exact-observation experiments; posted prices and the 16 noisy allocation samples for the sampled-observation experiment.
- **Cournot experiment**: two firms, known linear inverse demand, observed equilibrium quantities, unknown common marginal cost. Output one recovered cost per instance.
- Do not use any instance's ground truth (budgets, costs, or the true equilibrium allocation of the sampled-observation experiment) as an input when producing that instance's estimate. The labeled training split may be used to develop and tune a method.
- Predict every training and test instance exactly once, with finite values in the parameter domain (budgets > 0, costs >= 0), and use the same `method` name in every experiment.

## Compliance Checklist

- [ ] Uses only the observation fields of each instance (no `budgets`, `marginal_cost`, or true `allocation` of noisy instances) to form its estimate.
- [ ] Leaves the files under `data/` unchanged.
- [ ] Writes predictions for all four experiments, covering every training and test ID once.
- [ ] Reports parameter accuracy and exploitability through `scripts/evaluate_train.sh` / `scripts/evaluate.sh`.
