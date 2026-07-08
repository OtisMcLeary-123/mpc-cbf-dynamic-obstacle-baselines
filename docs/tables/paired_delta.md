# Paired ED-vs-CBF Delta Table

Deltas are matched by seed and computed as `CBF gamma=0.08 - ED`.

| Suite | Scenario | Backend | Seeds | Δsuccess | Δcollision | Δclearance | Δpath length | Δsolve time |
|---|---|---|---:|---:|---:|---:|---:|---:|
| exp_e4 | point_mass_2d_dynamic_obstacle_v1 | random_shooting | 3 | 0.333 ± 0.653 | 0.000 ± 0.000 | 0.749 ± 0.017 | -0.096 ± 0.987 | 0.033 ± 0.008 |
| extended/backend_comparison/casadi | point_mass_2d_dynamic_obstacle_v1 | casadi | 20 | 0.850 ± 0.161 | -0.850 ± 0.161 | 0.627 ± 0.006 | 2.385 ± 0.379 | -0.375 ± 1.699 |
| extended/backend_comparison/random_shooting | point_mass_2d_dynamic_obstacle_v1 | random_shooting | 20 | -0.050 ± 0.224 | 0.000 ± 0.000 | 0.761 ± 0.037 | 0.715 ± 0.448 | 0.039 ± 0.006 |
| extended/prediction_noise/prediction_noise_0.00 | prediction_noise_0.00 | random_shooting | 20 | -0.050 ± 0.224 | 0.000 ± 0.000 | 0.761 ± 0.037 | 0.715 ± 0.448 | 0.029 ± 0.007 |
| extended/prediction_noise/prediction_noise_0.03 | prediction_noise_0.03 | random_shooting | 20 | 0.050 ± 0.224 | -0.050 ± 0.098 | 1.050 ± 0.071 | 1.735 ± 0.474 | 0.027 ± 0.026 |
| extended/prediction_noise/prediction_noise_0.06 | prediction_noise_0.06 | random_shooting | 20 | -0.500 ± 0.266 | -0.050 ± 0.098 | 1.112 ± 0.066 | 3.665 ± 0.571 | 0.022 ± 0.015 |
| extended/prediction_noise/prediction_noise_0.10 | prediction_noise_0.10 | random_shooting | 20 | -0.750 ± 0.195 | -0.050 ± 0.098 | 0.972 ± 0.119 | 5.235 ± 0.497 | 0.042 ± 0.020 |
| extended/scenarios/diagonal_crossing_v1_random_shooting | diagonal_crossing_v1 | random_shooting | 50 | -0.040 ± 0.096 | 0.000 ± 0.000 | 0.586 ± 0.018 | 0.579 ± 0.274 | 0.040 ± 0.005 |
| extended/scenarios/fast_crossing_v1_random_shooting | fast_crossing_v1 | random_shooting | 50 | -0.260 ± 0.175 | 0.000 ± 0.000 | 0.602 ± 0.022 | 1.274 ± 0.342 | 0.046 ± 0.004 |
| extended/scenarios/large_obstacle_v1_random_shooting | large_obstacle_v1 | random_shooting | 50 | 0.000 ± 0.097 | -0.020 ± 0.039 | 0.594 ± 0.034 | 0.714 ± 0.270 | 0.043 ± 0.006 |
| extended/scenarios/late_crossing_v1_random_shooting | late_crossing_v1 | random_shooting | 50 | 0.020 ± 0.105 | 0.000 ± 0.000 | 0.762 ± 0.023 | 1.010 ± 0.289 | 0.038 ± 0.004 |
| extended/scenarios/noisy_prediction_v1_random_shooting | noisy_prediction_v1 | random_shooting | 50 | -0.440 ± 0.160 | -0.040 ± 0.055 | 0.986 ± 0.035 | 3.460 ± 0.338 | 0.043 ± 0.005 |
| extended/scenarios/point_mass_2d_dynamic_obstacle_v1_random_shooting | point_mass_2d_dynamic_obstacle_v1 | random_shooting | 50 | 0.020 ± 0.131 | 0.000 ± 0.000 | 0.765 ± 0.024 | 0.643 ± 0.281 | 0.043 ± 0.006 |
| extended/scenarios/short_horizon_v1_random_shooting | short_horizon_v1 | random_shooting | 50 | 0.040 ± 0.055 | -0.040 ± 0.055 | 0.624 ± 0.015 | 0.712 ± 0.165 | 0.027 ± 0.005 |
| extended/speed_sweep/obstacle_speed_0.20 | obstacle_speed_0.20 | random_shooting | 20 | -0.050 ± 0.224 | 0.000 ± 0.000 | 0.726 ± 0.042 | 0.335 ± 0.401 | 0.075 ± 0.027 |
| extended/speed_sweep/obstacle_speed_0.35 | obstacle_speed_0.35 | random_shooting | 20 | -0.050 ± 0.224 | 0.000 ± 0.000 | 0.761 ± 0.037 | 0.715 ± 0.448 | 0.032 ± 0.017 |
| extended/speed_sweep/obstacle_speed_0.50 | obstacle_speed_0.50 | random_shooting | 20 | -0.400 ± 0.220 | 0.000 ± 0.000 | 0.634 ± 0.037 | 1.385 ± 0.525 | 0.023 ± 0.010 |
| extended/speed_sweep/obstacle_speed_0.65 | obstacle_speed_0.65 | random_shooting | 20 | -0.450 ± 0.265 | 0.000 ± 0.000 | 0.396 ± 0.049 | 1.695 ± 0.459 | 0.026 ± 0.009 |
| extended/stress_100_seeds/base_random_shooting | point_mass_2d_dynamic_obstacle_v1 | random_shooting | 100 | -0.080 ± 0.095 | 0.000 ± 0.000 | 0.771 ± 0.016 | 0.760 ± 0.193 | 0.037 ± 0.002 |
| paper_main/e4_base_50_seed | point_mass_2d_dynamic_obstacle_v1 | random_shooting | 50 | 0.020 ± 0.131 | 0.000 ± 0.000 | 0.765 ± 0.024 | 0.643 ± 0.281 | 0.023 ± 0.006 |
