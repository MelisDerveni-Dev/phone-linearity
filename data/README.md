# Measurement manifest

| Export (unchanged, in `raw/`) | Runs · samples | Content | Role |
| --- | --- | --- | --- |
| `Acceleration with g 2026-10-21 17-43-29` | 12 · 172,447 | Six faces, each recorded twice in a row | 1st repeat fits, 2nd tests |
| `Acceleration with g 2026-10-22 10-55-51` | 9 · 131,834 | Ramps at 38.68° and 18.21° (screen-up and on side, two runs each), then 31 s of shaking | Held-out validation; shaking is the limit experiment |
| `Acceleration with g 2026-10-23 11-40-57` | 4 · 57,686 | Screen-up ramps at 0/4/8/11 cm, L = 16 cm | Held-out validation |

All exports: Samsung SM-S938B, Android 16, phyphox 1.2.1, "Acceleration with g", STMicro LSM6DSV (reported range ±156.9064 m/s², resolution 0.0047856 m/s²), 473.5 Hz observed. Every sample of every export is an integer multiple of that resolution. Results that use these files: `python -m calib analyse` (static and 22 Oct), `python scripts/validate_new_angles.py` (23 Oct) and `python -m calib evidence` (model comparison, linearity test, limits). See the root [README](../README.md#one-command-per-result). Each export keeps phyphox's folder name rather than the brief's `team_pose_session.csv` pattern, because one export holds several runs. `recordings.csv` and the split manifests map every run to its pose or angle.

## New four-height validation: 23 October

The new untouched export is `raw/Acceleration with g 2026-10-23 11-40-57/`, with four START/PAUSE runs of 29.76–31.55 s and **57,686 samples**. The user confirms one screen-up orientation throughout, heights **0, 4, 8 and 11 cm**, and the same **16 cm hypotenuse**. These give nominal references **0°, 14.4775°, 30°, 43.4325°**. Table rest is explicitly on camera bumps, so the first reference is nominal 0°, not an independently levelled phone body.

```powershell
python scripts/validate_new_angles.py
```

The command reads the existing fitted JSON and frozen static-training policy with exact input-hash checks. It does **no fitting or threshold tuning**. It reuses strict CSV/event validation and the original half-open acquisition boundaries. All original numeric strings/rows are retained in the ignored, reproducible `processed/angles-2026-10-23/validation.csv`, with provenance and reversible inclusion flags. The frozen policy retains **53,673 samples**; compact hashes, boundaries, counts and protocol are in [the acquisition audit](splits/angles-2026-10-23/README.md). New large generated data remains ignored; ignore rules are unchanged.

See [new measured results](../results/angle-validation-2026-10-23/README.md) and its figures. Equal-weight four-run tilt RMSE is **3.988562° raw / 4.110647° corrected**. Raised-only sensitivity is **4.604338° / 4.740403°**, so the nominal-zero caveat does not change the conclusion. One acquisition per height provides four distinct settings, with no within-setting repeatability estimate. The raw export, frozen calibration/policy, notebook and earlier experiments are unchanged. No cause for the angle discrepancy is uniquely established.

**Measurements collected on 21–23 October 2026.** The first export contains twelve static start/pause recordings. The second contains eight quiet angle runs and one shaking run; the third has the four new height settings described above. Static fitting and the first validation are in [the original analysis](../results/analysis-2026-10-23/README.md); `python -m calib analyse` generates separate masks without editing acquisition splits. Limits (quantization, full scale, shaking) are quantified in [the evidence results](../results/evidence-2026-10-23/README.md); no independent dynamic reference exists, so shaking is reported as a failure of the gravity-only model, not of S and b. New validation uses `python scripts/validate_new_angles.py` with the frozen fit. The live viewer does not save or alter raw recordings.

## Angle/shaking export: 22 October

Source: `raw/Acceleration with g 2026-10-22 10-55-51/Raw Data.csv` and original `meta/` files. There are **131,834 samples** in nine acquisition intervals, each **30.001–32.542 s**. Device/sensor metadata matches the first export. Four consecutive quiet pairs have alternating training/testing acquisition labels. They are validation data for the affine model fitted on the six static faces, not training data for a second model. These are within-session repeats. Run 9 is shaking, retained separately and in full.

```powershell
python scripts/preprocess_angles.py "data/raw/Acceleration with g 2026-10-22 10-55-51"
python -m unittest discover -s tests -p "test_*.py" -v
```

The Windows interpreter fallback documented below also works for these commands. The standard-library script reuses the strict exported-header reader and original START/PAUSE partitioner. Outputs under `processed/angles-2026-10-22/` are `training.csv` (58,204 rows), `testing.csv` (58,885), and `limit.csv` (14,745). All original numeric strings and timestamps are preserved. Added source-row, segment/pair, split, support orientation, geometry and inclusion fields make exclusions reversible. `include=1` selects `[START+1 s, PAUSE-1 s)` in quiet runs: **54,440 training** and **55,122 testing** samples. This fixed timing precaution was chosen before error evaluation, removes no interior outliers, and is not rest detection or proof of stillness. All 14,745 shaking rows have `include=1`; never interpret that flag as a stationary label.

The user confirms the phone makes a right triangle with **16 cm along its length as the hypotenuse**, and wall heights **10 cm** (runs 1–4) and **5 cm** (runs 5–8). Thus `asin(h/L)` gives **38.6822°** and **18.2100°** relative to horizontal. Runs 1–2 and 5–6 are screen-up; runs 3–4 and 7–8 are on the side with the screen perpendicular to the table. This is recorded in the [protocol](splits/angles-2026-10-22/protocol.json). Exact signed reference vectors, case/rate settings and ruler/contact uncertainties remain unspecified. This export alone has two distinct heights; the 23 October export adds four more (0–43.4°).

Git preserves the hashed protocol's exact bytes, as it does for raw sources, so its audit hash remains valid across Windows/Linux checkouts.

See [audit](splits/angles-2026-10-22/README.md), [manifest](splits/angles-2026-10-22/manifest.json) and [trace review](splits/angles-2026-10-22/trace-review.svg). The review uses shared quiet-panel scales and a separately labelled shaking scale, preserving pixel extrema. Quiet per-axis standard deviations are about 0.008–0.011 m/s²; this describes signal variability, not accuracy. The shaking vector magnitude reaches **119.821 m/s²**. No independent dynamic force reference is available, so this shows the limit of gravity-only tilt interpretation, not affine sensor failure. The peak per-axis value is 94.3 m/s², 60 % of the reported full scale, so no clipping occurs. Raw files remain unchanged; the generated training/testing/limit CSVs are versioned at the user's request alongside the script/protocol/audit. Narrow ignore exceptions cover only these three angle datasets; Git preserves their exact bytes for audit hashes.

Use phyphox **Acceleration with g**, on one phone with a consistent case configuration. Its physical accelerometer includes the gravity reference. Do not use **Acceleration (without g)** for the static calibration.

Keep that standard experiment/settings for comparable scientific ramp collection. The separate **Affine Observatory – motion** demo requests acceleration at 100 Hz and fused attitude at 50 Hz; its fused estimate uses the phone's internal orientation sensors, including the gyroscope. Switching to it changes the acquisition configuration relative to this first static export. Export existing data before switching and document any scientific recordings made with different settings instead of silently pooling them. The 3D model represents orientation, not measured position; a translational shake need not produce a rotation.

The export metadata identifies Samsung SM-S938B (Galaxy S25 Ultra), Android 16, phyphox 1.2.1, and `lsm6dsv_0 Accelerometer Non-wakeup` (STMicro). Case configuration and the user-selected sampling setting are unconfirmed. Observed cadence is approximately 473.5 Hz; this is measured delivery cadence, not a confirmed rate setting. The device metadata's sensor range is not evidence of clipping in this recording.

| Export field | Header observed in actual CSV | Unit |
| --- | --- | --- |
| Time | `Time (s)` | s |
| Phone x acceleration | `Acceleration x (m/s^2)` | m/s² |
| Phone y acceleration | `Acceleration y (m/s^2)` | m/s² |
| Phone z acceleration | `Acceleration z (m/s^2)` | m/s² |
| Vector magnitude | `Absolute acceleration (m/s^2)` | m/s² |

## Static inventory and split

Source: `raw/Acceleration with g 2026-10-21 17-43-29/Raw Data.csv`, with its original `meta/time.csv` and `meta/device.csv`. Acquisition was 17:33:33–17:43:20 UTC+02:00; the folder timestamp is the export time. The 172,447 data rows span 364.30 s of recorded sample time. Timestamps are strictly increasing and all fields are finite.

The event log confirms **twelve recordings lasting 29.34–32.06 s**. The measured chronological order is **+Y, +Y, -Y, -Y, -X, -X, +X, +X, +Z, +Z, -Z, -Z**. Labels refer to the dominant measured component. All six directions are present. The user authorizes nominal ±g references and reports steady support with rear-camera contact screen-up and a button-bearing side; exact alignment remains uncertain.

The first complete repeat of each pose is **training (86,323 samples)**; the second is **testing (86,124 samples)**. Acquisition events define exact half-open `[START, PAUSE)` intervals, rather than guesses at 30-second boundaries. Phyphox experiment time excludes the wall-clock pauses. No samples are dropped, duplicated, trimmed, smoothed, resampled, or corrected. Original timestamps and the five original numeric strings remain in the outputs; appended provenance columns identify the 1-based source data row (excluding the header), run, observed pose, repeat and split.

These are **within-session repeat holdouts**, not independently collected sessions A/B. The metadata does not prove the phone was independently repositioned between repeats. Keep the split fixed; do not tune future preprocessing/model choices using testing errors. Use independent ramp recordings for additional validation and collect independently repositioned repeats if the course requires separate sessions.

From the project root, with Python 3.10 or newer:

```powershell
python scripts/split_static_recording.py "data/raw/Acceleration with g 2026-10-21 17-43-29"
```

On this Windows setup, if the Python command/launcher alias is unavailable, use:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" scripts/split_static_recording.py "data/raw/Acceleration with g 2026-10-21 17-43-29"
```

No Python dependencies are needed. This regenerates `processed/static-2026-10-21/training.csv` and `testing.csv`, plus the shared [audit and boundary table](splits/static-2026-10-21/README.md). [manifest.json](splits/static-2026-10-21/manifest.json) records hashes, exact boundaries, descriptive pose statistics and limitations. At the user's request, both training/testing CSVs are versioned alongside the raw export, script and audit so teammates can use them immediately. Narrow ignore exceptions include only these two derived datasets; other processed artifacts stay ignored. Git preserves the datasets' exact bytes to keep hashes consistent across checkouts. Re-running replaces derived outputs only. This script is deliberately specific to the twelve-recording consecutive-repeat protocol; it rejects ambiguous or incomplete protocols instead of inventing assignments.

Verify the split utility with `python -m unittest discover -s tests -p "test_static_split.py" -v` (also compatible with pytest). Five tests cover exact boundary assignment, whole-repeat holdout, numeric-string/raw-byte preservation, invalid input, and incomplete/mismatched repeats. The general reader and rest-period detector are in `src/calib/data.py`, tested in `tests/test_calib.py` and `tests/test_evidence.py`.

## Original collection plan (20–21 October, kept for reference)

Status: the static faces, two ramp sessions (six distinct angles from 0° to 43.4°) and the shaking limit run were collected. Rest masks were implemented with training-only choices. A second static session, a stationary drift run and an independently referenced limit experiment were not collected (see the report's limits section).

1. Assign session A to `fit` and session B to `test` before inspecting errors. Model selection and threshold tuning use session A only.
2. The first static export supplies two roughly 30 s repeats per face. The brief's planned approximately 20 s is a target, not a reason to truncate the longer recordings. Next implement/review rest masks using training choices only; preserve start/stop handling for documented exclusion. Additional independent static sessions should use supported edges and explicit repositioning.
3. Record at least four known ramp angles across 0° to 45°, for example 0°, 15°, 30°, 45°. A practical set is one flat recording, then 15°/30°/45° along phone X and along phone Y: seven recordings, 30 s each. Optional opposite-direction ramps add negative X/Y checks. Keep the screen up and the selected axis along the board's steepest slope, with no sideways tilt; keep contact/support and case consistent, accounting for the camera bump. Measure vertical height difference h between supports and their spacing L **along the board**. Then theta = asin(h/L). Use actual measured angles, not nominal targets or the phone's own inclination reading. Document direction/sign, h, L and ruler uncertainty. Let the phone settle before recording, do not touch it during acquisition, and stop before repositioning. These are held-out validation files, not fitting/tuning data.
4. Record a limit candidate with an independent reference. First candidate: long stationary recording in one securely supported pose; compare stable windows for drift. Optional temperature comparison must document the condition and keep pose unchanged. Shaking alone does not prove accelerometer nonlinearity, since actual input changes. If a candidate does not fail, retain and report it and choose another justified candidate.
5. Export original decimal-point CSVs. Name files `team_pose_session.csv`, for example `team_zplus_A.csv`, after confirming actual pose signs. If phyphox exports a ZIP, preserve it and its CSV contents without editing the exported bytes. Add one metadata row per original CSV; document the archive association in notes.

`data/recordings.csv` has one metadata row for the original mixed-pose export, not twelve invented source filenames. `filename` is relative to `data/`; interval assignments live in the split manifest. Required course fields are included, plus split, reference components, device/settings, and ruler uncertainty. Use SI units except the explicitly labelled degree column. Unknown values stay blank; exact reference vectors are not inferred from accelerometer readings. `pose` means the actual signed reference orientation when confirmed, or `mixed` for this multi-pose source.

Never overwrite files in `raw/`. A bad recording remains raw; record a replacement and explain it in notes. Rest masks, pose means and intermediate calculations belong in `processed/`. Figures and metrics belong in `results/`.

The dashboard has a bounded in-memory history (120 s, at most 30,000 samples). It is a viewer, not the evidence archive: **export every recording from phyphox separately**.
