# Angle and shaking acquisition: 22 October 2026

All original rows are retained in versioned, reproducible split CSVs. Use `include=1` for the timing-trimmed quiet-run summaries; no automated rest detector is claimed.

| Run | Pair | Support | Split | Seconds | All / included samples | Height (m) | Angle (degrees) |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | 1 | screen_up | training | 31.070 | 14705 / 13765 | 0.1 | 38.68218745348944 |
| 2 | 1 | screen_up | testing | 30.802 | 14577 / 13637 | 0.1 | 38.68218745348944 |
| 3 | 2 | on_side_screen_perpendicular | training | 30.001 | 14200 / 13259 | 0.1 | 38.68218745348944 |
| 4 | 2 | on_side_screen_perpendicular | testing | 30.649 | 14507 / 13565 | 0.1 | 38.68218745348944 |
| 5 | 3 | screen_up | training | 31.478 | 14898 / 13958 | 0.05 | 18.20995686428301 |
| 6 | 3 | screen_up | testing | 30.422 | 14399 / 13458 | 0.05 | 18.20995686428301 |
| 7 | 4 | on_side_screen_perpendicular | training | 30.423 | 14401 / 13458 | 0.05 | 18.20995686428301 |
| 8 | 4 | on_side_screen_perpendicular | testing | 32.542 | 15402 / 14462 | 0.05 | 18.20995686428301 |
| 9 | None |  | limit | 31.153 | 14745 / 14745 | None | None |

Angles use asin(height / contact spacing), relative to horizontal, only when both geometry fields are supplied. User-confirmed contact spacing is 16 cm along the phone (the hypotenuse), with 10 cm height for runs 1–4 and 5 cm for runs 5–8. Thus angles are 38.6822 and 18.2100 degrees. Runs 1–2 and 5–6 are screen-up; runs 3–4 and 7–8 are on the side, screen perpendicular to the table. The shaking run has no reference angle. Unknown heights/spacing stay blank in CSVs. Do not infer independent geometry from sensor readings.

See `manifest.json` for hashes, exact times, per-run statistics and limitations; `trace-review.svg` shows all runs, with excluded boundary regions shaded. Each quiet panel uses the same axis scale; shaking uses its own labelled scale to retain extremes. Pixel-column min/max envelopes preserve spikes.

Training/testing are acquisition labels; ramps remain separate from six-face calibration fitting.
Pairs come from one session; independent repositioning not confirmed.
Timing trim is not rest detection; inspect the audit plot and per-run variability.
Screen-up versus side support is user-confirmed; exact signed reference vectors and ruler/contact uncertainty remain unspecified.
Shaking changes true input and invalidates gravity-only tilt interpretation; it does not establish affine accelerometer failure.
No fitting, corrected errors, improvement or clipping conclusion.
