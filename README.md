# The Affine Observatory

### Is your phone linear?

**Authors: Melis Derveni and Harsimranjeet Kaur.** Melis carried out measurements and experiments and prepared the other deliverables, including the report, README and live demonstration. Harsimranjeet developed model training, testing and evaluation. Both worked on the project and jointly discussed and agreed the approach, model and analysis choices. See [contributions and joint tradeoffs](docs/team-contributions.md).

A small laboratory for a big question: **can one affine model describe your phone's accelerometer?** A live phyphox viewer pairs the phone's original signal with the same signal after an affine correction, in a parchment-and-brass instrument panel inspired by a scientist turning gears.

**Current milestone · 23 October 2026.** A separate Python analysis extends the teammate's unchanged regression notebook. The nominal static-repeat vector RMSE improves from **0.215965 to 0.111114 m/s²**, while the new four-height held-out tilt RMSE is **3.988562° raw / 4.110647° corrected**. Earlier angle results remain recorded separately. A measured four-page report, tests, figures, and viewer-compatible fitted JSON are ready. Physical fitted-phone rehearsal, geometry uncertainty, signatures and a referenced affine-failure case remain outstanding.

**For teammates and coding agents:** read [AGENTS.md](AGENTS.md) first for the current status, architecture, scientific rules, collaboration workflow, and next milestones.

## Reproduce the measured analysis

Python 3.10+ is separate from the dependency-free Node viewer. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,report]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m calib.analysis
.\.venv\Scripts\python.exe scripts/validate_new_angles.py
npm.cmd --prefix report ci
.\.venv\Scripts\python.exe report/build_report.py
```

On macOS/Linux use `.venv/bin/python` instead. If Windows' `python` alias is unavailable, use the explicit interpreter fallback in [data/README.md](data/README.md). The analysis verifies acquisition hashes, freezes the stability policy using static training only, fits equal-weight pose means, and evaluates static/angle holdouts without retuning. It reproduces the original notebook's full-row result separately. No notebook or source CSV is edited.

The new four-height command loads the existing frozen calibration/policy; it does not train. Those archived inputs and the acquisition protocol retain exact Git bytes for their audit hashes. A differently regenerated fit is intentionally rejected by this fixed-model evaluation.

Read [static analysis](results/analysis-2026-10-23/README.md), [new four-height validation](results/angle-validation-2026-10-23/README.md), [the four-page report](report/report-draft.pdf), and [the rehearsal guide](docs/demo-rehearsal.md). The four PNGs and compact result tables/JSON are versioned under `results/analysis-2026-10-23/`; large per-sample masks remain ignored and reproducible under `data/processed/analysis-2026-10-23/`. Existing ignore rules are unchanged.

To run the demo with the measured fit:

```powershell
npm.cmd start -- --calibration calibration/fit-static-2026-10-21.json
```

`npm start` works outside the Windows PowerShell restriction. The fit comes from six nominal ±g poses, including placement uncertainty; it does **not** establish universal accuracy improvement. Both angle acquisition labels are validation only. The demo keeps identity as the default when no calibration is supplied.

## Run the live observatory

Install [Node.js](https://nodejs.org/) 22 or newer. No npm packages, API keys, online fonts or build step are needed.

```powershell
npm start
```

**Windows PowerShell:** if `npm start` reports that `npm.ps1` cannot be loaded because running scripts is disabled, use the Windows command launcher instead:

```powershell
npm.cmd start
```

This does not require changing PowerShell's execution policy. You can also start the viewer directly with `node scripts/live.mjs`. Run these commands from the project root, where `package.json` lives.

The script opens `http://127.0.0.1:5173` in your browser. On Windows, `scripts/start-live.ps1` is another option when your PowerShell policy allows scripts. Keep the terminal running.

1. Connect phone and laptop to the same Wi-Fi or phone hotspot.
2. In phyphox, select **Acceleration with g**. Enable **Allow remote access** in the experiment menu and keep the experiment open.
3. Copy the exact HTTP address displayed by phyphox into the dashboard and select **Connect**. Include the displayed port. Private IPv4 URLs are supported; do not infer the port from the phone type.
4. Use the large **Start phone** and **Stop phone** buttons above the graphs. They are available in both the main dashboard and the display window. Start is enabled when the connected phone is paused; Stop is enabled while it is measuring. Connecting alone never starts or clears the phone.
5. Select **Display window** to open both graphs together in a separate browser window. Move it to your presentation screen. Fullscreen and a compact display layout are available. Allow the popup if your browser blocks it.

Raw and corrected graphs share time limits, axis visibility and vertical scale. The initial correction is **identity / uncalibrated**, so the graphs agree exactly. Once a real fit exists, load its JSON using **Load calibration** or the command below. Imported coefficients without training provenance are marked unverified; the viewer cannot establish their scientific validity.

The bridge requests new phone samples up to 20 times per second, depending on network latency, and pushes incremental updates to each window over a persistent local event stream. Charts animate between batches at the browser's refresh rate. Dense traces retain per-pixel minima and maxima so narrow spikes remain visible; no sensor smoothing is applied. Each window keeps the latest 32 seconds for plotting, while the bridge retains its larger bounded history. A first connection/reconnection sends a window of history once; subsequent messages contain only new points and status.

## Present the calibration

The presentation section pairs two inclination dials with a focused comparison graph. In **Display window**, the instruments and graph sit side by side on a wide screen. Expand **Full three-axis traces** below to inspect the original plots.

1. Choose **Along phone X** or **Along phone Y** for the dials. These show signed inclination of that acceleration component relative to the other two components, from -90° to +90°. Keep the phone supported and still when interpreting this as tilt.
2. Select **Tilt**, **X**, **Y** or **Z** in the comparison panel. **Correction applied** shows corrected minus raw on a tighter, explicitly labelled scale. **Raw & corrected** overlays just the selected measurement with a shared scale. Neither view alone establishes improved accuracy.
3. For a reference comparison, enter an independently measured angle in degrees, or a known component value in m/s² for X/Y/Z. Confirm **Phone held still at this reference**, then start/resume the phone. The graph switches to **Error vs reference**, with zero as the reference line. A ruler-supported 0° is appropriate only when you have independently established that the selected slope is level.
4. The cards show **current-sample** raw/corrected absolute errors and their difference. A positive reduction means less error; a negative value means more error. These are not held-out accuracy scores or aggregate validation results.

Reference comparisons begin with fresh samples after confirmation. Uncheck the confirmation before moving the phone or changing the ramp. Changing the reference, focus, slope direction, calibration or stream resets the confirmation. Settings synchronize between windows in the same browser. With identity calibration, the dials match and the applied correction/error reduction is zero. Synthetic preview remains labelled; it never becomes phone evidence.

## The 3D phone

Below the original X/Y/Z trace inspector is **The phone, in motion**. Starting a fresh measurement opens the trace inspector and reveals an authored Samsung Galaxy S25 Ultra model against a transparent, fixed XYZ plane. The body uses Samsung's published **162.8 × 77.6 × 8.2 mm** proportions, with illustrative titanium framing, screen, camera rings and ports. It is a locally authored visual approximation, not manufacturer CAD. There are no external model downloads or rendering dependencies. [Samsung specifications](https://www.samsung.com/ca/smartphones/galaxy-s25-ultra/specs/).

With **Acceleration with g**, the model follows calibrated **gravity-based tilt**. Acceleration alone cannot identify rotation about gravity (heading), nor recover phone position. Drag the stage to orbit the viewing camera; **Reset view** restores the camera without changing sensor data or calibration. Pausing retains the last pose. Disconnection resets the view; stale data holds the last pose with a warning.

During strong motion, the view flags **tilt uncertainty** using the current vector magnitude and the vector RMS variation over the last 0.25 s. Indicator thresholds are 0.35 m/s² for noticeable deviation/variation and 1.5 m/s² for strong deviation/variation relative to approximately g = 9.81 m/s². These are display heuristics, not a calibrated confidence score or an automatic rest detector. Even a near-g, quiet vector does not prove the phone is still. The pose interpolates timestamped measurements through a fixed **70 ms display buffer**, preserving intermediate acceleration/attitude poses between network batches instead of easing toward only the latest sample. No rotation is extrapolated beyond measured endpoints. Reduced-motion preferences display the latest pose directly. Gravity tracking continues from the preceding pose to avoid arbitrary heading jumps near screen-down; that displayed heading remains unmeasured. Plots and numerical samples are unchanged. Render/transport latency can also limit tracking. The motion pause described below is an explicitly labelled display safeguard, not simulated sensor failure.

At the user's request, **fast motion now pauses the displayed phone pose**, with a red border, warning banner and slowly pulsing warning symbol. It triggers only when the current vector magnitude exceeds 60 m/s², or quaternion-derived angular speed exceeds 720°/s over 0.15 s. The lower motion-indicator thresholds do not freeze the model. Tracking resumes after 0.15 s of fresh measurements with magnitude below 30 m/s² and, when attitude is available, angular speed below 180°/s. An 80 ms blend returns the model to the current measured pose; full stillness is not required. Reduced-motion preferences disable pulsing/blending. The plots and phone acquisition continue throughout.

This is an **intentional display policy**, labelled on screen, not a measured failure threshold; fused attitude may continue tracking correctly during the hold. Shaking can invalidate the assumption that acceleration gives gravity direction. This does **not**, by itself, establish a failure of the affine sensor model. Keep that distinction in the report and demo.

### Optional: full rotation with fused attitude

For heading as well as tilt, open [observatory-motion.phyphox](experiments/observatory-motion.phyphox) on your phone and import it into phyphox. You can download it from the 3D section while the dashboard runs, then transfer/open the file on the phone. Select **Affine Observatory - motion**, enable its remote access, and reconnect using the URL it shows. Export any existing recording before switching experiments. Importing the file through the phyphox experiment editor, the phone's file picker or a shared file is sufficient; no browser device-orientation permission is used.

This configuration requests physical acceleration with gravity at 100 Hz and optional OS-fused attitude at 50 Hz. When a compatible attitude stream is detected, the view selects **Fused attitude** automatically; you can switch back to **Gravity tilt** to compare their assumptions. Missing attitude leaves gravity mode available. Attitude uses its own timestamp buffer; it is never paired by acceleration-array index. The scalar quaternion component comes from phyphox's `abs` output, following the [official sensor documentation](https://phyphox.org/docs/file-format/input/).

If two rotations follow but the third stays still, check **ORIENTATION SOURCE**: the standard **Acceleration with g** experiment supplies no attitude stream. Open the full-rotation setup panel below the model. **Export existing recordings first**, then return to phyphox's experiment list and use **+ → Add experiment from QR code**. Scan the displayed QR: it embeds the complete motion experiment and works offline. Open **Affine Observatory – motion**, enable remote access there, reconnect using its displayed URL, and press Start phone. The browser cannot enable sensors absent from the active phone experiment. A downloadable file remains available if you prefer file import. See the [official transfer instructions](https://phyphox.org/docs/transferring-experiments/).

The QR SVG is a checked-in static asset. Only rebuilding it needs the optional build dependency: `python -m pip install "qrcode>=8,<9"`, then `python scripts/build_motion_qr.py`. Rebuild after changing the experiment file. It encodes a ZIP with phyphox's 13-byte offline header and CRC32, not a web address; no external QR service or dashboard runtime dependency is used. Its payload structure/ZIP round-trip are verified by the generator; physical scanning/import still needs verification on the phone.

Fused attitude is the device's estimate, not independent ground truth or an affine correction. It uses the phone's internal sensors, including the gyroscope; phyphox is the transport. It still does not measure position, so a translational shake need not produce a model rotation. The optional experiment's XML and mock-phone integration are checked; importing and validating this configuration on your physical S25 Ultra remains a demo preparation step. Record the chosen experiment/rates in your metadata and keep settings consistent across fit and test sessions. For comparable scientific ramp collection, keep the standard Acceleration with g configuration used by the static export; the combined demo's requested rates differ.

```powershell
npm start -- --phone http://192.168.1.42:8080 --calibration calibration/params.json
```

The address above is an example: substitute the actual URL. An explicit buffer override is available for custom experiments; inspect `/config` first:

```powershell
npm start -- --phone http://192.168.1.42:8080 --buffers acc_time,accX,accY,accZ
```

Other options: `--port 5174`, `--no-open`, `--help`. A **synthetic preview** can exercise the display without a phone. It is labelled throughout, starts only on request, and is never recorded or presented as experimental evidence. Enabling it disconnects the viewer from the phone; it does not stop the phone. Disconnecting or closing this viewer also does not stop a running phyphox experiment.

Connecting to a long recording first requests only the latest acceleration/attitude timestamps, then downloads the last 32 s of acceleration and 0.5 s of attitude before incremental polling. It does not request the entire phone archive or clear it to avoid a response-size error. Export the complete recording from phyphox separately.

**Export every experimental recording from phyphox separately.** The viewer holds only 120 s / 30,000 points in memory and never writes into `data/raw/`. Keep the phone awake and phyphox in the foreground. A stale stream, paused experiment, missing buffers and network errors are shown explicitly. A changed experiment session clears the live history and requires reconnection. A bridge restart discards viewer history and any calibration loaded only through the UI.

If connection fails, open the displayed phyphox URL directly in your browser. Check remote access, address, port, same Wi-Fi, VPN settings and guest-network client isolation. The bridge listens on loopback only, so other devices do not need access to the laptop server.

## The model

```text
Measured:     m = S a + b
Corrected:    a_hat = solve(S, m - b)
```

S is a dimensionless 3×3 matrix of gains and cross-axis terms. b is a three-axis offset in m/s². This is affine when b is nonzero. Calibration is not noise removal or gravity separation; no fixed matrix can recover information lost to clipping.

The current JSON format is:

```json
{
  "schema_version": 1,
  "name": "Phone / session A",
  "fitted": true,
  "units": "m/s^2",
  "S": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
  "b": [0, 0, 0],
  "provenance": {"training_session": "A", "files": ["actual-training-file.csv"]}
}
```

This example describes the schema, **not fitted measurements**. Use `calibration/identity.json` for an explicit uncalibrated reference. Uploads reject nonfinite values, wrong dimensions, wrong units, singular matrices and severely ill-conditioned matrices.

## Project map

```text
report/                 Scientific report draft, editable source and PDF
data/raw/               Untouched phone exports and original device/event metadata
data/processed/         Reproducible training/testing CSVs; future rest masks/tables
data/splits/            Compact split audit, exact boundaries and source/output hashes
data/README.md          Inventory, split command, collection protocol and open questions
data/recordings.csv     One metadata row per original recording CSV
src/calib/              Affine class, strict CSV reader, stability masks and analysis CLI
calibration/            Identity JSON; future fitted parameters
experiments/            Optional acceleration + fused-attitude phyphox configuration
results/analysis-2026-10-23/ Measured metrics, provenance and four evidence figures
results/figures/        Other future evidence plots
results/metrics/        Future held-out metrics
web/                    Local dashboard HTML, CSS and JavaScript
scripts/                Node live bridge, Windows launcher and Python split utility
tests/                  Live bridge and calibration-application checks
decisions.md            Decisions, alternatives and evidence
```

Read [the typeset report](report/report-draft.pdf), open [the self-contained KaTeX HTML](report/report.html), or edit [the LaTeX/Markdown source](report/report.md). See [report build instructions](report/README.md). Document-only KaTeX/Markdown tooling and Python Playwright produce the four-page PDF; the live viewer still needs no npm install or Python.

## Verification

```powershell
npm test
npm run check
```

Tests exercise known affine correction, invalid calibration, official phyphox-style buffer discovery, a mock phone with incremental samples, start/stop, reconnect/session handling, event streaming to two windows, bounded client history, spike-preserving trace reduction, signed tilt, correction versus reference error, orientation quaternion math, physical phone proportions, independent attitude timestamps, and HTTP boundaries. They do not establish the accuracy of a real phone. The separate Python pytest suite covers CSV validation, stability masks, training-only policy selection, affine recovery, JSON round-trip and deficient/invalid inputs. Node and Python tests establish implementation behavior, not physical sensor accuracy.

## Reproduce the static dataset split

For the newer angle/shaking export, run:

```powershell
python scripts/preprocess_angles.py "data/raw/Acceleration with g 2026-10-22 10-55-51"
python -m unittest discover -s tests -p "test_*.py" -v
```

See [the angle audit](data/splits/angles-2026-10-22/README.md) and [trace review](data/splits/angles-2026-10-22/trace-review.svg). Four consecutive training/testing pairs remain separate from six-face calibration fitting; the ninth run is shaking. The same future affine model will be tested on these angles, without fitting a second model. Angles from confirmed 16 cm contact spacing are 38.6822° (10 cm height) and 18.2100° (5 cm). All original samples survive with source-row provenance. Quiet-run `include=1` excludes one second at each acquisition boundary; this is not a scientific rest detector. The generated training/testing/limit CSVs are versioned at the user's request, with narrow ignore exceptions and exact-byte preservation for audit hashes. Shaking alone does not establish affine sensor failure.

With Python 3.10 or newer, from the project root:

```powershell
python scripts/split_static_recording.py "data/raw/Acceleration with g 2026-10-21 17-43-29"
python -m unittest discover -s tests -p "test_static_split.py" -v
```

No Python dependencies are required for this utility. It uses the twelve START/PAUSE intervals to retain complete recordings: first of each pose pair trains, second tests. Outputs: `data/processed/static-2026-10-21/training.csv` (86,323 samples) and `testing.csv` (86,124 samples). The original export is unchanged; no preprocessing or fitting has been done. [Read the audit](data/splits/static-2026-10-21/README.md) and [data protocol](data/README.md), including the Windows interpreter fallback. These repeats came from one collection session; independent ramp validation is still required. Both CSVs are included in Git at the user's request and remain reproducible from source. Other processed artifacts stay ignored; dataset bytes are preserved across checkouts for hash verification.

## Remaining physical and submission steps

- Verify case/sampling consistency and ruler/contact uncertainty; explain the recorded geometry disagreement without changing held-out references to match the phone.
- Rehearse the fitted JSON on the physical phone, including separate display, start/stop and honest reference comparisons.
- Four distinct height settings are now recorded (0/4/8/11 cm). Nominal zero rests on camera bumps; add repeats if estimating repeatability. Establish an independently referenced limit experiment before claiming affine sensor failure.
- Melis Derveni and Harsimranjeet Kaur should sign and date the measured report; their names and contributions are recorded.
- Preserve the negative angle result and the slight worsening of the -Z static vector error. The current report emphasises the static calibration benefit while stating the angle limitation concisely. More tuning requires new training data and new validation.

## References and course logistics

The supplied course PDF, *Sprint project: Is your phone linear?* (18 October 2026), is the requirements source. It is not republished here. It contains conflicting deadline statements: the schedule says 23 October at 12:00; later pages say “Fri 28 Oct, 8:00”. Confirm the deadline and Q&A duration with the course team.

API integration follows the official [phyphox remote-interface reference](https://phyphox.org/docs/remote-interface/) and its [OpenAPI schema](https://phyphox.org/docs/remote-interface/openapi.yaml). The distinction between physical acceleration with gravity and gravity-removed virtual acceleration follows the [phyphox sensor documentation](https://phyphox.org/docs/file-format/input/).
