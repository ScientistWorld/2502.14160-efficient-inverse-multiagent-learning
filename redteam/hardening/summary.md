| case | kind | train rank delta | test rank delta | noisy recovery (test) | noisy mean rel L2 (test) | failures (test) |
|---|---|---:|---:|---:|---:|---|
| reference_seed7 | reference | +0 | +0 | 0.605 | 0.0930 | - |
| reference_seed8 | reference | -0.00178952 | +4.0351e-05 | 0.605 | 0.0930 | - |
| reference_seed9 | reference | +0.00207651 | +0.0020478 | 0.610 | 0.0930 | - |
| weaker_training | weaker_variant | -18.7742 | -18.5722 | 0.000 | 0.9379 | - |
| stronger_training | stronger_variant | +0.000680519 | +0.000498208 | 0.605 | 0.0931 | - |
| closed_form_arithmetic_pooling | honest_alternative | -0.13313 | -0.136349 | 0.340 | 0.1274 | - |
| closed_form_log_pooling | honest_alternative | -0.011113 | -0.00887546 | 0.585 | 0.0945 | - |
| closed_form_single_sample | honest_alternative | -0.856119 | -1.04978 | 0.035 | 0.3733 | - |
| shipped_baseline_observed_expenditure | baseline | -21.6031 | -21.6063 | 0.340 | 0.1274 | cournot_cost_recovery |
| better_clearing_constrained_demo | better_variant | +0.141714 | +0.164887 | 0.910 | 0.0437 | - |
| shortcut_label_copy | shortcut | +0.235463 | -107.108 | 0.000 | 1.0000 | fisher_cd_budget_recovery, fisher_linear_budget_recovery, cournot_cost_recovery, fisher_cd_noisy_budget_recovery |
| shortcut_cherry_pick | shortcut | -107.115 | -107.108 | 0.000 | 1.0000 | fisher_cd_budget_recovery, fisher_linear_budget_recovery, cournot_cost_recovery, fisher_cd_noisy_budget_recovery |
| shortcut_rewrite_labels | shortcut | +0.214796 | +0 | 0.605 | 0.0930 | - |
| shortcut_replace_fixed_data | shortcut | +0.235463 | -10.8701 | 0.005 | 0.8360 | - |
| shortcut_forged_scores_flags | shortcut | -14.6362 | -10.8701 | 0.005 | 0.8360 | - |
| shortcut_constant | shortcut | -14.6362 | -10.8701 | 0.005 | 0.8360 | - |
| shortcut_zero | shortcut | -94.9576 | -94.4831 | 0.000 | 1.0000 | fisher_cd_budget_recovery, fisher_linear_budget_recovery, fisher_cd_noisy_budget_recovery |
| shortcut_negative | shortcut | -107.115 | -107.108 | 0.000 | 1.0000 | fisher_cd_budget_recovery, fisher_linear_budget_recovery, cournot_cost_recovery, fisher_cd_noisy_budget_recovery |
| shortcut_empty | shortcut | -107.115 | -107.108 | 0.000 | 1.0000 | fisher_cd_budget_recovery, fisher_linear_budget_recovery, cournot_cost_recovery, fisher_cd_noisy_budget_recovery |
| shortcut_null | shortcut | -107.115 | -107.108 | 0.000 | 1.0000 | fisher_cd_budget_recovery, fisher_linear_budget_recovery, cournot_cost_recovery, fisher_cd_noisy_budget_recovery |
| shortcut_nan | shortcut | n/a | n/a | nan | nan | - |
| shortcut_inf | shortcut | n/a | n/a | nan | nan | - |
| shortcut_drop_hard_experiment | shortcut | -42.7052 | -42.6984 | 0.000 | 1.0000 | fisher_cd_noisy_budget_recovery |
| shortcut_one_nan_row | shortcut | -42.7052 | -42.6984 | 0.000 | 1.0000 | fisher_cd_noisy_budget_recovery |
| shortcut_subset_coverage | shortcut | +0 | -107.108 | 0.000 | 1.0000 | fisher_cd_budget_recovery, fisher_linear_budget_recovery, cournot_cost_recovery, fisher_cd_noisy_budget_recovery |

Seed spread of the reference (max-min test rank delta over seeds 7/8/9): 0.0020478043293597125
