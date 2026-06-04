# Constraints

For comparable scores, keep the generated game and market instances fixed unless explicitly creating a new experiment.

The Fisher benchmark uses 3 buyers, 2 unit-supply goods, Cobb-Douglas utilities with known utility types, and unknown buyer budgets. Methods may change the optimization routine, initialization, or numerical implementation, but they must output recovered budgets for the same observed allocations, prices, and utility types. Do not use the true budgets as inputs to the method.

The Cournot benchmark uses fixed two-firm games with known linear inverse demand and observed equilibrium quantities. Methods must output one recovered marginal cost per game for the same observed quantities and demand parameters. Do not use the true marginal cost as a method input.

## Compliance Checklist

- [ ] Uses the benchmark's fixed observed allocations, prices, and utility types.
- [ ] Uses the benchmark's fixed observed Cournot quantities and demand parameters when evaluating Cournot.
- [ ] Does not use the true budgets or marginal costs as method inputs.
- [ ] Reports both parameter accuracy and exploitability through `scripts/evaluate.sh`.
