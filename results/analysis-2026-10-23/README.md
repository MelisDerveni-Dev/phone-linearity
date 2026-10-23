# Measured analysis: 23 October 2026

Extends the teammate's notebook regression in separate files; notebooks and acquisition datasets are unchanged. Regenerate with `python -m calib.analysis` after editable installation.

## Static repeat holdout

Mean vector error: 0.201209 -> 0.105644 m/s². Vector RMSE: 0.215965 -> 0.111114 m/s².

Magnitude RMSE: 0.078677 -> 0.048051 m/s². Direction RMSE: 1.173729 -> 0.585285 degrees. All metrics average six pose means equally; these are nominal-reference, within-session results.

## Angle validation

Unsigned long-axis tilt RMSE: **3.267287 -> 3.726342 degrees** over eight run means. No full-vector reference is invented from measured signs. Both acquisition-labelled training/testing angle files are validation only.

| Run | Support | Reference ° | Raw ° | Corrected ° | Raw absolute error ° | Corrected absolute error ° |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | screen_up | 38.6822 | 35.1190 | 35.1399 | 3.5632 | 3.5423 |
| 2 | screen_up | 38.6822 | 35.1196 | 35.1405 | 3.5626 | 3.5417 |
| 3 | on_side_screen_perpendicular | 38.6822 | 35.4956 | 34.7300 | 3.1866 | 3.9522 |
| 4 | on_side_screen_perpendicular | 38.6822 | 35.4926 | 34.7270 | 3.1896 | 3.9551 |
| 5 | screen_up | 18.2100 | 14.5611 | 14.1727 | 3.6488 | 4.0372 |
| 6 | screen_up | 18.2100 | 14.5595 | 14.1710 | 3.6505 | 4.0389 |
| 7 | on_side_screen_perpendicular | 18.2100 | 15.6562 | 14.8845 | 2.5538 | 3.3254 |
| 8 | on_side_screen_perpendicular | 18.2100 | 15.6559 | 14.8843 | 2.5541 | 3.3257 |

## Parameters and quality checks

```json
{
  "schema_version": 1,
  "name": "S25 Ultra / nominal six-face fit",
  "units": "m/s^2",
  "S": [
    [
      0.9995617676140324,
      -0.00806341675930164,
      0.015705674678177243
    ],
    [
      0.00559739515603771,
      0.9978696357353594,
      0.0034396663436530093
    ],
    [
      -0.0031543423765676933,
      0.0058916569615257985,
      0.9984467069877514
    ]
  ],
  "b": [
    -0.05074012467767164,
    0.06856265722531751,
    0.10431595915664345
  ],
  "fitted": true,
  "provenance": {
    "training_session": "static-2026-10-21 / first within-session repeats",
    "files": [
      "data/processed/static-2026-10-21/training.csv"
    ],
    "training_sha256": "c4a7e2bd8fb64e4fc407f06ad3846e03120c23ee1b30ca219960515afb66cb6a",
    "reference": "Nominal six +/-9.81 m/s^2 axes; placement uncertainty includes rear cameras and side buttons.",
    "method": "Equal-weight pose means; forward least squares via NumPy SVD; notebook regression retained.",
    "gravity_m_s2": 9.81,
    "stability_threshold_m_s2": 0.05,
    "stability_policy": "0.25 s local vector RMS; threshold=max(0.05,training median+8*1.4826*MAD); 1 s boundary trim, 1 s minimum interval; gaps >0.1 s break continuity."
  },
  "diagnostics": {
    "rank": 4,
    "singular_values": [
      13.873435046880065,
      13.873435046880063,
      13.873435046880063,
      2.449489742783178
    ],
    "design_condition": 5.66380614075023,
    "dimensionless_design_condition": 1.732050807568877,
    "S_condition": 1.0159506349186154
  }
}
```

Masks are reproducible, ignored derived artifacts under data/processed/analysis-2026-10-23. The 0.25 s RMS threshold is frozen on static training; fixed 1 s boundary trim and 1 s minimum stable interval apply unchanged to validation. Signal variation does not certify exact alignment or stationarity.

Included static samples: 80677 training and 80474 testing.

## Limits

- Static tests are within-session repeats, not independent sessions.
- Nominal +/-g references include support alignment error; fit is not intrinsic sensor identification.
- Ruler resolution, contact uncertainty, case and user-selected rate remain unconfirmed.
- Ramps use unsigned long-axis tilt only; signed full reference vectors are not independently established.
- Only two ramp angles; no confirmed affine-model failure; live physical rehearsal pending.
- Low variation is a rest heuristic, not proof of stationarity.

Shaking is a limit of gravity-only interpretation, not proof of affine sensor failure. Review all four PNGs; positive and negative changes are retained. No thresholds or coefficients were revised after evaluating held-out errors.
