# Decision log

Each entry records what we decided, which alternatives we considered, and the evidence. Entries are in chronological order.

## 20 Oct · Sensor and hypothesis
**Decision:** record with the phyphox experiment *Acceleration with g* and test the affine model m = S a + b with a full 3×3 S.
**Alternatives:** *Acceleration (without g)*; a diagonal S (gains only).
**Evidence:** the gravity-removed experiment deletes the signal we calibrate against. The full S is the model in the course brief; a diagonal S is the special case with no cross-axis terms.

## 20 Oct · Training and test split fixed before collecting data
**Decision:** record every static pose twice; the first recording trains, the second tests. All tilted (ramp) recordings are test data only.
**Alternatives:** a random split of samples; choosing test poses after seeing errors.
**Evidence:** neighbouring samples are almost identical, so a random split would leak training data into the test. Fixing the roles in advance keeps the test honest.

## 21 Oct · Six static poses, split by the phone's own start/stop events
**Decision:** six poses (±x, ±y, ±z up), about 30 s each. Recordings are separated using the START/PAUSE events phyphox exports, and every raw file is kept unchanged.
**Alternatives:** cutting the file into fixed 30 s blocks by hand; fewer poses.
**Evidence:** the event log gives exact boundaries for all 12 recordings (172,447 samples, 86,323 training and 86,124 testing). Six poses make the design matrix rank 4, which the 12 unknowns require; four poses are the minimum, and the extra two give a check.

## 23 Oct · Rest periods chosen on training data only
**Decision:** drop the first and last second of each recording, and keep only stretches of at least 1 s whose 0.25 s variation stays below a threshold. The threshold (0.05 m/s²) was set from the training recordings and frozen before any test file was read.
**Alternatives:** no trimming; a threshold tuned on test errors; discarding samples that disagree with the expected value.
**Evidence:** the rule keeps 93 % of training samples, and the masks were checked visually. Selecting samples by their error would bias the test, so we never do that.

## 22 Oct · Tilt test geometry
**Decision:** lean the 16 cm phone against a wall at measured heights and compute the angle from sin θ = h / L: 18° and 39° on 22 Oct, and 0°, 14°, 30° and 43° on 23 Oct. Heights are used exactly as measured.
**Alternatives:** using the phone's own reading as the reference; adjusting heights to match the phone.
**Evidence:** the ruler gives a reference independent of the sensor. Adjusting it to fit the phone would make the test meaningless.

## 23 Oct · Model: full affine fit by least squares (Harsimranjeet's model)
**Decision:** fit all 12 numbers of S and b by least squares on the six training pose averages (one average per pose, so every pose counts equally). Correct new readings with â = S⁻¹(m − b).
**Alternatives:** a bias-only model (3 numbers); a diagonal S (6 numbers); fitting every sample instead of pose averages.
**Evidence:** on the six held-out test poses, the error drops from 0.216 to 0.111 m/s² and the tilt error from 1.17° to 0.59°. Fitting pose averages stops longer recordings from dominating. After these results we also compared a diagonal-S version, which kept a still phone's reading closer to 9.81 on later days (0.023 vs 0.058 m/s²) but had a larger static test error (0.184 vs 0.111 m/s²). Because that comparison came after the results were known, we did not switch models on its basis; the full model remains our calibration. All variants are listed in `results/evidence-2026-10-23/`.

## 23 Oct · How we test linearity
**Decision:** use the fact that a still phone must read exactly 9.81 m/s² at any angle. Each axis sees only part of gravity on the tilted recordings; if its response were not proportional, the calibrated reading would drift away from 9.81 at in-between angles.
**Alternatives:** compare tilt angles with the ruler only.
**Evidence:** the calibrated reading stays within 0.07 m/s² of 9.81 on all held-out recordings, as close at in-between angles as at the training poses. The ruler comparison is reported separately: the phone reads 3–6° below the ruler angle with or without calibration, and calibration moves it by less than 1°, so this gap does not come from the sensor.

## 23 Oct · Failure experiment
**Decision:** shake the phone hard for 30 s and report it as the case where the model fails, because the reading is no longer gravity alone.
**Alternatives:** a long still recording to look for drift; heating the phone.
**Evidence:** the reading reaches 120 m/s² and stays far from 9.81 almost the whole time (only 0.6 % of samples within 0.35 m/s²). Without a second instrument we cannot tell whether the sensor itself became nonlinear, so we do not claim that. The phone's sensor limit is 157 m/s² (16 g); our peak per axis was 94 m/s², so nothing was clipped.

## 23 Oct · Reproducible results
**Decision:** one command per result (`python -m calib analyse`, `python scripts/validate_new_angles.py`, `python -m calib evidence`, `python -m calib fit`, `python -m calib apply`). The saved calibration file is checked against a fresh fit, never silently overwritten, and a file is marked as fitted only when it really was.
**Alternatives:** rerunning a notebook by hand; regenerating the calibration file on every run.
**Evidence:** a fresh fit matches the saved file to within 1e-9, and the saved file's checksum stays the same on Windows and Linux. 26 Python tests pass, including one that recovers a known S and b from synthetic data.

## 23 Oct · Live demo
**Decision:** a local viewer streams the phone's readings and shows raw and calibrated values side by side on the same scales, with a spirit-level dial. Without a calibration file it stays uncalibrated, and it warns when the phone moves.
**Alternatives:** a hosted web page; showing only the calibrated signal.
**Evidence:** the phone's data stay on the local network, and shared scales prevent the correction from looking better than it is. 33 viewer tests pass; the physical rehearsal is still to do.
