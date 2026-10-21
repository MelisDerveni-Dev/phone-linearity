# Measurement manifest

**Static measurements collected on 21 October 2026.** One original export contains twelve start/pause recordings: two consecutive repeats of each of the six signed axis poses. Angle and referenced limit measurements remain pending. The live viewer does not save or alter raw recordings.

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

The event log confirms **twelve recordings lasting 29.34–32.06 s**. The measured chronological order is **+Y, +Y, -Y, -Y, -X, -X, +X, +X, +Z, +Z, -Z, -Z**. Labels refer to the dominant measured component. All six directions are present; physical support alignment still needs confirmation before assigning exact reference vectors.

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

Verify the split utility with `python -m unittest discover -s tests -p "test_static_split.py" -v` (also compatible with pytest). Five tests cover exact boundary assignment, whole-repeat holdout, numeric-string/raw-byte preservation, invalid input, and incomplete/mismatched repeats. This is not the deferred general calibration loader/rest detector.

## Remaining collection and preprocessing

1. Assign session A to `fit` and session B to `test` before inspecting errors. Model selection and threshold tuning use session A only.
2. The first static export supplies two roughly 30 s repeats per face. The brief's planned approximately 20 s is a target, not a reason to truncate the longer recordings. Next implement/review rest masks using training choices only; preserve start/stop handling for documented exclusion. Additional independent static sessions should use supported edges and explicit repositioning.
3. Record at least four known ramp angles across 0° to 45°, for example 0°, 15°, 30°, 45°. A practical set is one flat recording, then 15°/30°/45° along phone X and along phone Y: seven recordings, 30 s each. Optional opposite-direction ramps add negative X/Y checks. Keep the screen up and the selected axis along the board's steepest slope, with no sideways tilt; keep contact/support and case consistent, accounting for the camera bump. Measure vertical height difference h between supports and their spacing L **along the board**. Then theta = asin(h/L). Use actual measured angles, not nominal targets or the phone's own inclination reading. Document direction/sign, h, L and ruler uncertainty. Let the phone settle before recording, do not touch it during acquisition, and stop before repositioning. These are held-out validation files, not fitting/tuning data.
4. Record a limit candidate with an independent reference. First candidate: long stationary recording in one securely supported pose; compare stable windows for drift. Optional temperature comparison must document the condition and keep pose unchanged. Shaking alone does not prove accelerometer nonlinearity, since actual input changes. If a candidate does not fail, retain and report it and choose another justified candidate.
5. Export original decimal-point CSVs. Name files `team_pose_session.csv`, for example `team_zplus_A.csv`, after confirming actual pose signs. If phyphox exports a ZIP, preserve it and its CSV contents without editing the exported bytes. Add one metadata row per original CSV; document the archive association in notes.

`data/recordings.csv` has one metadata row for the original mixed-pose export, not twelve invented source filenames. `filename` is relative to `data/`; interval assignments live in the split manifest. Required course fields are included, plus split, reference components, device/settings, and ruler uncertainty. Use SI units except the explicitly labelled degree column. Unknown values stay blank; exact reference vectors are not inferred from accelerometer readings. `pose` means the actual signed reference orientation when confirmed, or `mixed` for this multi-pose source.

Never overwrite files in `raw/`. A bad recording remains raw; record a replacement and explain it in notes. Rest masks, pose means and intermediate calculations belong in `processed/`. Figures and metrics belong in `results/`.

The dashboard has a bounded in-memory history (120 s, at most 30,000 samples). It is a viewer, not the evidence archive: **export every recording from phyphox separately**.
