# Measurement manifest

**No phone data has been collected for this repository yet.** Collection is planned for 21 October 2026. The live viewer does not save or alter raw recordings.

Use phyphox **Acceleration with g**, on one phone with a consistent case configuration. Its physical accelerometer includes the gravity reference. Do not use **Acceleration (without g)** for the static calibration.

Before recording, enter the phone model, OS, phyphox version, case configuration, sampling settings, and observed axis convention here. Confirm exported column labels and units from an actual export; do not assume their exact spelling.

| Export field | Header observed in actual CSV | Unit |
| --- | --- | --- |
| Time | Pending first export | s |
| Phone x acceleration | Pending first export | m/s² |
| Phone y acceleration | Pending first export | m/s² |
| Phone z acceleration | Pending first export | m/s² |

## Plan for tomorrow

1. Assign session A to `fit` and session B to `test` before inspecting errors. Model selection and threshold tuning use session A only.
2. Record six static faces, approximately 20 s each. Repeat all six in session B. Support edges with a book; avoid touching during a stable interval. Preserve start/stop handling for subsequent documented exclusion.
3. Record at least four known ramp angles from 0° to 45°. Measure vertical height h and support spacing L **along the board**. Then theta = asin(h/L). Document rotation axis, ruler uncertainty and signs. These are held-out validation files.
4. Record a limit candidate with an independent reference. First candidate: long stationary recording in one securely supported pose; compare stable windows for drift. Optional temperature comparison must document the condition and keep pose unchanged. Shaking alone does not prove accelerometer nonlinearity, since actual input changes. If a candidate does not fail, retain and report it and choose another justified candidate.
5. Export original decimal-point CSVs. Name files `team_pose_session.csv`, for example `team_zplus_A.csv`, after confirming actual pose signs. If phyphox exports a ZIP, preserve it and its CSV contents without editing the exported bytes. Add one metadata row per original CSV; document the archive association in notes.

`data/recordings.csv` currently contains headers only. Required course fields are included, plus split, reference components, device/settings, and ruler uncertainty. Use SI units except the explicitly labelled degree column. Unknown numeric values stay blank. `pose` means the actual signed reference orientation, not an unchecked face label.

Never overwrite files in `raw/`. A bad recording remains raw; record a replacement and explain it in notes. Rest masks, pose means and intermediate calculations belong in `processed/`. Figures and metrics belong in `results/`.

The dashboard has a bounded in-memory history (120 s, at most 30,000 samples). It is a viewer, not the evidence archive: **export every recording from phyphox separately**.
