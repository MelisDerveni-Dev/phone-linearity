# Static recording split: 21 October 2026

Twelve START/PAUSE recordings confirm two consecutive repeats of each signed axis. Labels describe the dominant **measured** component, not independently verified reference alignment.

| Run | Observed pose | Assignment | Duration (s) | Samples | Source data rows |
| --- | --- | --- | ---: | ---: | --- |
| 1 | +Y | training | 29.341 | 13,888 | 1-13888 |
| 2 | +Y | testing | 29.745 | 14,080 | 13889-27968 |
| 3 | -Y | training | 29.384 | 13,909 | 27969-41877 |
| 4 | -Y | testing | 30.035 | 14,218 | 41878-56095 |
| 5 | -X | training | 30.140 | 14,267 | 56096-70362 |
| 6 | -X | testing | 29.715 | 14,066 | 70363-84428 |
| 7 | +X | training | 30.538 | 14,455 | 84429-98883 |
| 8 | +X | testing | 30.117 | 14,256 | 98884-113139 |
| 9 | +Z | training | 32.064 | 15,176 | 113140-128315 |
| 10 | +Z | testing | 30.916 | 14,635 | 128316-142950 |
| 11 | -Z | training | 30.904 | 14,628 | 142951-157578 |
| 12 | -Z | testing | 31.415 | 14,869 | 157579-172447 |

Training: **86,323 samples**. Testing: **86,124 samples**. All **172,447** source samples are assigned exactly once, with no overlap or omitted rows.

The first five fields retain the original numeric strings and experiment timestamps. Added columns identify the source data row, acquisition run, observed pose, repeat and split. Source data row 1 is physical CSV line 2. No trimming, smoothing, resampling, fitting or error-based selection was performed.

`manifest.json` records source/output SHA-256 hashes, exact event boundaries, wall-clock acquisition times, descriptive medians/standard deviations and checks. `segments.csv` provides a compact boundary table. The training/testing CSVs in `data/processed/static-2026-10-21/` are versioned at the user's request; regenerate them using the command in `data/README.md`. Git preserves their exact bytes so hashes also match in a fresh checkout.

The raw CSV has strictly increasing finite timestamps and finite acceleration values. Maximum absolute difference between the exported magnitude and the vector norm: 9.9e-10 m/s². These inventory checks do not certify metrological accuracy or establish that every sample is stationary.

## Before calibration

These are within-session repeat holdouts, not independent collection sessions. In particular, pauses do not prove independent repositioning. Keep the assignment fixed, tune future preprocessing on training only, and use independently measured ramps as additional holdout validation. Confirm support alignment, case and sampling settings. Implement and review rest masks before fitting. Ramp recordings and a referenced limit experiment remain pending.
