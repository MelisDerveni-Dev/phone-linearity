# Is your phone linear? · The Affine Observatory

**Authors: Melis Derveni and Harsimranjeet Kaur.** Melis performed the measurements and experiments and prepared the report, README, live demonstration and other deliverables. Harsimranjeet developed model training, testing and evaluation. Both jointly discussed and agreed the approach, model and analysis decisions ([details](docs/team-contributions.md)).

We calibrate the accelerometer of one Samsung Galaxy S25 Ultra with phyphox, test the affine hypothesis **m = S a + b** on recordings the model never saw, and show where it stops holding. The repository holds the untouched recordings, a Python package with a fit/apply class, tests, one command per result, a four-page report and a live phone-to-screen demo.

📄 **[Read the report (PDF, 4 pages)](report/report.pdf)** · [decision log](decisions.md) · [data protocol](data/README.md) · [evidence tables](results/evidence-2026-10-23/README.md)

## Results: the five questions

| Question | Answer from our data |
| --- | --- |
| **1 · In which sense is it linear?** | **Affine, not linear**: a straight line plus an offset. The fitted offset is b = (−0.051, 0.069, 0.104) m/s². With an extra coordinate, `[m;1] = [[S,b],[0,1]] [a;1]` is linear. Estimating S and b is a linear least-squares problem whatever the sensor does. |
| **2 · How do you know?** | A still phone must read 9.81 m/s² at any angle. The model was trained only with gravity along one axis. On tilted recordings from later days, where each axis feels 20–98 % of gravity, the calibrated reading stays within 0.07 m/s² of 9.81, as close as at the training poses. |
| **3 · Which poses?** | Six poses, each axis once up and once down, give the design matrix rank 4, which the 12 unknowns need. Without a screen-up or screen-down pose the rank drops to 3 and the z response cannot be found. |
| **4 · How much does it help?** | On held-out test poses the error drops from 0.22 to 0.11 m/s², and the tilt error from 1.2° to 0.6°. On the wall ramps the phone reads 3–6° below the ruler angle with or without calibration; calibration moves it by less than 1°, so the gap does not come from the sensor. |
| **5 · Where does it break?** | When the phone moves. Shaking reaches 120 m/s², so the gravity-only model fails. The sensor also clips above 157 m/s² (never reached) and counts in steps of 0.005 m/s². |

**Calibration:** [`calibration/fit-static-2026-10-21.json`](calibration/fit-static-2026-10-21.json), Harsimranjeet's full affine least-squares fit (12 numbers). `results/evidence-2026-10-23/` also lists simpler variants (bias-only, diagonal S) for comparison; they are not used.

## Quick start

Python 3.10+ for the analysis; Node.js 22+ for the live viewer. From the repository root:

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\python.exe   ·   macOS/Linux: .venv/bin/python
python -m pip install -e ".[test]"
python -m pytest                       # 26 tests, including synthetic recovery of known S and b
```

## One command per result

| Result | Command | Output |
| --- | --- | --- |
| Static split of the 21 Oct export | `python scripts/split_static_recording.py "data/raw/Acceleration with g 2026-10-21 17-43-29"` | `data/processed/static-2026-10-21/`, `data/splits/static-2026-10-21/` |
| Ramp/shaking split of the 22 Oct export | `python scripts/preprocess_angles.py "data/raw/Acceleration with g 2026-10-22 10-55-51"` | `data/processed/angles-2026-10-22/`, `data/splits/angles-2026-10-22/` |
| Rest masks, frozen policy, full fit, static and 22 Oct held-out metrics | `python -m calib analyse` | [`results/analysis-2026-10-23/`](results/analysis-2026-10-23/README.md) |
| Four-height validation (23 Oct) with the frozen fit | `python scripts/validate_new_angles.py` | [`results/angle-validation-2026-10-23/`](results/angle-validation-2026-10-23/README.md) |
| Linearity test, model comparison, repeatability, limits | `python -m calib evidence` | [`results/evidence-2026-10-23/`](results/evidence-2026-10-23/README.md) |
| Fit S and b on the training repeats | `python -m calib fit --out calibration/params.json` | JSON parameters (the full 12-number model) |
| Apply a calibration to any new phyphox export | `python -m calib apply calibration/fit-static-2026-10-21.json "<export folder>" --out results/applied/corrected.csv` | Corrected CSV plus per-run tilt and \|â\| summary |
| Report PDF/HTML | `npm --prefix report ci` then `python -m pip install -e ".[report]"` and `python report/build_report.py` | `report/report.pdf`, `report/report.html` |

Run them in this order. `analyse` **verifies** the archived fit and frozen policy (values within 1e-9) instead of rewriting them, so the hash-checked inputs of `validate_new_angles.py` keep their exact bytes on every platform. Use `--refreeze` only to replace them deliberately. On Windows PowerShell, use `npm.cmd` if `npm.ps1` is blocked.

## How it works

```text
measured   m = S a + b                 S: 3x3 gains and cross-axis terms, b: bias (m/s^2)
corrected  a_hat = solve(S, m - b)     never an explicit inverse of a fitted design
```

1. **Read** each export unchanged (`calib.data`): strict SI headers, START/PAUSE intervals, row provenance.
2. **Find rest periods**: drop 1 s at each boundary; keep stable ≥ 1 s intervals whose 0.25 s RMS vector variation is below a threshold chosen on training data only (0.05 m/s²). The threshold is frozen before any held-out file is read.
3. **Fit** (`calib.model.AffineCalibration.fit`) on six equal-weight training pose means by SVD least squares. Use `structure="full"` (12 parameters, rank 4 required; our model). `structure="diagonal"` exists for comparison only.
4. **Evaluate** on held-out data with identical windows for raw and corrected.

The JSON format is shared with the live viewer:

```json
{"schema_version": 1, "name": "...", "units": "m/s^2", "S": [[...],[...],[...]], "b": [...],
 "fitted": true, "provenance": {"training_session": "...", "files": ["..."]}, "diagnostics": {...}}
```

`fitted` is stored explicitly and never inferred from metadata. Loading rejects wrong units, nonfinite or singular matrices, and `fitted: true` without provenance. [`calibration/identity.json`](calibration/identity.json) is the explicit uncalibrated reference.

## Data

All three original exports in [`data/raw/`](data/raw) are unchanged (Git stores their exact bytes; every script checks SHA-256 hashes). They contain 361,967 samples at 473.5 Hz from one SM-S938B phone:

- **21 Oct, static:** six faces, each recorded twice in a row. The first repeat fits, the second tests (within one session).
- **22 Oct, ramps:** 18.2° and 38.7°, screen-up and on side, two runs each; plus 31 s of shaking as the limit experiment.
- **23 Oct, ramps:** 0, 14.5, 30.0 and 43.4° (h = 0/4/8/11 cm, L = 16 cm), screen-up.

See [`data/README.md`](data/README.md) for the protocol, column names and units, and [`data/recordings.csv`](data/recordings.csv) for one metadata row per file.

## Live demo

```bash
npm start -- --calibration calibration/fit-static-2026-10-21.json     # Windows PowerShell: npm.cmd start -- ...
```

This opens `http://127.0.0.1:5173`. In phyphox choose **Acceleration with g**, enable remote access, and enter the phone's URL. The dashboard shows raw and corrected traces on shared axes, inclination dials, and an error-vs-reference view for a still phone at a ruler-measured angle. A spirit-level check takes four steps:

1. Lay the phone flat and confirm it is still.
2. Raise one end by a measured height h over contact distance L.
3. Enter asin(h/L) as the reference.
4. Compare the raw and corrected dials.

Without `--calibration` the viewer stays on identity, labelled *uncalibrated*. For an offline backup, record in phyphox, export, and run `python -m calib apply` on the export. Full viewer documentation is in [`docs/live-viewer.md`](docs/live-viewer.md); the rehearsal checklist is in [`docs/demo-rehearsal.md`](docs/demo-rehearsal.md).

## Tests and checks

```bash
python -m pytest      # 26 Python tests (+8 subtests)
npm test              # 33 Node tests for the live bridge, plotting, orientation and calibration application
npm run check         # syntax checks for the viewer scripts
```

The Python tests cover:

- recovery of a known full S and b, and of a diagonal S and b under simulated support tilt;
- rank-deficient pose sets and invalid parameters;
- JSON round-trip and the explicit `fitted` flag;
- reader validation;
- stability masks and training-only policy freezing;
- frozen-artifact verification across newline styles;
- that the linearity test has power against a 0.5 % compression;
- that the validation path never fits.

Tests establish implementation behaviour, not physical accuracy.

## Limitations

- The static repeats come from **one session**, so they test reproducibility of nearly the same placement: repeats agree to 0.002 m/s² for five of six faces. The two later sessions test only the reading size and tilt.
- Each pose assumes gravity lies exactly along one axis. The phone rests slightly tilted (for example on its camera bump), so some cross-axis terms in S may describe that tilt rather than the sensor.
- On the wall ramps the phone reads 3–6° below the ruler angle. We keep h and L exactly as measured; the geometric cause is not isolated.
- Linearity above 1 g has no independent reference. Shaking shows that the gravity assumption fails, not that the sensor is non-affine.
- Case and sampling settings were not logged (473.5 Hz observed); there is one run per 23 Oct height.
- The physical live demo with the fitted JSON still needs a rehearsal on the phone, and the report still needs signatures.

## Repository map

```text
report/            report.md (source) → report.pdf, report.html; build_report.py
src/calib/         AffineCalibration (model.py), readers and rest masks (data.py),
                   analyse (analysis.py), evidence (evidence.py), CLI (__main__.py)
scripts/           dataset splitters, frozen four-height validation, live bridge (live.mjs)
data/raw/          untouched phyphox exports (+ meta/device.csv, meta/time.csv)
data/processed/    reproducible splits (versioned at the team's request); masks are ignored
data/splits/       manifests with exact boundaries and source/output hashes
calibration/       identity (uncalibrated) and the fitted model (JSON)
results/           compact metrics, tables and figures for every command above
tests/             pytest suite and Node tests
web/               dashboard (HTML/CSS/JS, no dependencies)
docs/              live viewer, demo rehearsal, team contributions
decisions.md       decision log: decision, alternatives, evidence
main.ipynb         the original exploratory notebook (see below)
```

**About `main.ipynb`.** This is Harsimranjeet's original development notebook, kept byte-for-byte unchanged (`python -m calib analyse` records its hash and fails if it changes). It is not runnable from a clean start: cell 13 has an indentation error, it expects `training.csv`/`testing.csv` in the working directory, and it needs pandas and scikit-learn, which are not project dependencies. The package reproduces its regression exactly: `notebook_all_row_reproduction` in `results/analysis-2026-10-23/metrics.json`. Use the package commands above for every result.

## References and course logistics

Requirements come from the course brief *Sprint project: Is your phone linear?* (18 October 2026), which is not republished here. The brief states two deadlines: 23 October 12:00 in the schedule, and "Fri 28 Oct, 8:00" in the deliverables. Confirm with the course team. Sensor semantics follow the [phyphox input documentation](https://phyphox.org/docs/file-format/input/) and [remote interface](https://phyphox.org/docs/remote-interface/). For teammates and coding agents, [AGENTS.md](AGENTS.md) records the working rules and current status.
