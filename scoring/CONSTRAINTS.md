# Constraints

For comparable scores, keep the generated game and market instances fixed unless explicitly creating a new experiment.

The scored Fisher budget-only benchmarks use 3 buyers, 2 unit-supply goods, known utility types, and unknown buyer budgets. The accepted default utility families are Cobb-Douglas and linear. Methods may change the optimization routine, initialization, or numerical implementation, but they must output recovered budgets for the same observed allocations, prices, and utility types. Do not use the true budgets as inputs to the method.

The Cobb-Douglas type-and-budget benchmark uses the same 3-buyer, 2-good market structure, but methods must output both recovered budgets and recovered Cobb-Douglas type shares for the same observed allocations and prices. Do not use the true budgets or true type shares as method inputs.

The Cournot benchmark uses fixed two-firm games with known linear inverse demand and observed equilibrium quantities. Methods must output one recovered marginal cost per game for the same observed quantities and demand parameters. Do not use the true marginal cost as a method input.

The Bertrand benchmark uses fixed two-firm homogeneous-good games with known linear demand and observed equilibrium prices. Methods must output one recovered marginal cost per game for the same observed prices and demand parameters. Do not use the true marginal cost as a method input.

## Compliance Checklist

- [ ] Uses the benchmark's fixed observed allocations, prices, and utility types.
- [ ] Uses only the fixed observed allocations and prices for Cobb-Douglas type-and-budget recovery.
- [ ] Uses the benchmark's fixed observed Cournot quantities and demand parameters when evaluating Cournot.
- [ ] Uses the benchmark's fixed observed Bertrand prices and demand parameters when evaluating Bertrand.
- [ ] Does not use the true budgets or marginal costs as method inputs.
- [ ] Reports both parameter accuracy and exploitability through `scripts/evaluate.sh`.
