# Constraints

For comparable scores, keep the generated market instances fixed unless explicitly creating a new experiment. The current benchmark uses 3 buyers, 2 unit-supply goods, Cobb-Douglas utilities with known utility types, and unknown buyer budgets.

Methods may change the optimization routine, initialization, or numerical implementation, but they must output recovered budgets for the same observed allocations, prices, and utility types. Do not use the true budgets as inputs to the method.

## Compliance Checklist

- [ ] Uses the benchmark's fixed observed allocations, prices, and utility types.
- [ ] Does not use the true budgets as method inputs.
- [ ] Reports both parameter accuracy and exploitability through `scripts/evaluate.sh`.
