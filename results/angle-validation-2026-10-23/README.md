# Four-height validation: 23 October 2026

Frozen six-position calibration; no angle fitting or policy changes. All raw rows remain unchanged. Reproduce with `python scripts/validate_new_angles.py`.

| Height (cm) | Reference (°) | Raw (°) | Corrected (°) | Raw absolute error (°) | Corrected absolute error (°) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0000 | 0.1864 | 0.4188 | 0.1864 | 0.4188 |
| 4 | 14.4775 | 11.1414 | 10.6943 | 3.3361 | 3.7832 |
| 8 | 30.0000 | 25.9003 | 25.7249 | 4.0997 | 4.2751 |
| 11 | 43.4325 | 37.4607 | 37.5313 | 5.9718 | 5.9013 |

All four run means: **3.988562 -> 4.110647 degrees RMSE**.

Raised-only sensitivity (three run means): **4.604338 -> 4.740403 degrees RMSE**. This is a labelled subset, not a replacement headline or tuned selection.

57,686 samples; 53,673 included by the frozen 0.25 s RMS / 1 s boundary and duration policy. See manifest for exclusion counts and exact [START, PAUSE) intervals. The derived per-sample CSV is ignored and reproducible; compact audit/results and figures are shareable.

- The zero-height run rests on camera bumps; actual body level is not independently established.
- Each of four distinct heights has one acquisition; repeatability is not quantified within this new session.
- Measurement precision and case/rate consistency remain unspecified; reference values are retained as supplied.
- No retraining or threshold tuning; previous angle validation remains a separate recorded experiment.
- A worse tilt result is not uniquely attributed to sensor nonlinearity or reference error.
