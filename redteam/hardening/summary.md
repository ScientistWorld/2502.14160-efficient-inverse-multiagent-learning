| case | kind | before: test rank | after: train rank | after: test rank | test recovery CD / linear / Cournot / noisy | noisy mean rel L2 |
|---|---|---:|---:|---:|---|---:|
| reference_seed7 | reference | +0 | +0 | +0 | 1.000 / 1.000 / 1.000 / 0.605 | 0.093 |
| reference_seed8 | reference | +2.64076e-05 | -0.00178952 | +4.0351e-05 | 1.000 / 1.000 / 1.000 / 0.605 | 0.093 |
| reference_seed9 | reference | +1.98906e-05 | +0.00207651 | +0.0020478 | 1.000 / 1.000 / 1.000 / 0.610 | 0.093 |
| stronger_training | stronger_variant | +0.000612021 | +0.000680519 | +0.000498208 | 1.000 / 1.000 / 1.000 / 0.605 | 0.093 |
| weaker_training | weaker_variant | -10.6452 | -18.7742 | -18.5722 | 0.000 / 0.000 / 0.120 / 0.000 | 0.938 |
| better_clearing_constrained_demo | better_variant | not run | +0.141714 | +0.164887 | 1.000 / 1.000 / 1.000 / 0.910 | 0.044 |
| closed_form_arithmetic_pooling | honest_alternative | +0.000612021 | -0.13313 | -0.136349 | 1.000 / 1.000 / 1.000 / 0.340 | 0.127 |
| closed_form_log_pooling | honest_alternative | not run | -0.011113 | -0.00887546 | 1.000 / 1.000 / 1.000 / 0.585 | 0.095 |
| closed_form_single_sample | honest_alternative | not run | -0.856119 | -1.04978 | 1.000 / 1.000 / 1.000 / 0.035 | 0.373 |
| shipped_baseline_observed_expenditure | baseline | not run | -21.6031 | -21.6063 | 1.000 / 1.000 / failed / 0.340 | 0.127 |
| shortcut_cherry_pick | shortcut | +0.000612014 | -107.115 | -107.108 | failed / failed / failed / failed | failed |
| shortcut_constant | shortcut | -16.5809 | -14.6362 | -10.8701 | 0.000 / 0.000 / 0.080 / 0.005 | 0.836 |
| shortcut_drop_hard_experiment | shortcut | not run | -42.7052 | -42.6984 | 1.000 / 1.000 / 1.000 / failed | failed |
| shortcut_empty | shortcut | no finite rank | -107.115 | -107.108 | failed / failed / failed / failed | failed |
| shortcut_forged_scores_flags | shortcut | -16.5809 | -14.6362 | -10.8701 | 0.000 / 0.000 / 0.080 / 0.005 | 0.836 |
| shortcut_inf | shortcut | no finite rank | -107.115 | -107.108 | failed / failed / failed / failed | failed |
| shortcut_label_copy | shortcut | +0.000612021 | +0.235463 | -107.108 | failed / failed / failed / failed | failed |
| shortcut_nan | shortcut | no finite rank | -107.115 | -107.108 | failed / failed / failed / failed | failed |
| shortcut_negative | shortcut | -105.771 | -107.115 | -107.108 | failed / failed / failed / failed | failed |
| shortcut_null | shortcut | no finite rank | -107.115 | -107.108 | failed / failed / failed / failed | failed |
| shortcut_one_nan_row | shortcut | not run | -42.7052 | -42.6984 | 1.000 / 1.000 / 1.000 / failed | failed |
| shortcut_replace_fixed_data | shortcut | +0.000612021 | +0.235463 | -10.8701 | 0.000 / 0.000 / 0.080 / 0.005 | 0.836 |
| shortcut_rewrite_labels | shortcut | +0.000605985 | +0.214796 | +0 | 1.000 / 1.000 / 1.000 / 0.605 | 0.093 |
| shortcut_subset_coverage | shortcut | not run | +0 | -107.108 | failed / failed / failed / failed | failed |
| shortcut_zero | shortcut | -72.2112 | -94.9576 | -94.4831 | failed / failed / 0.000 / failed | failed |

Reference seed spread (max - min test rank over seeds 7/8/9): 0.0020478
