# The Affine Observatory

### Is your phone linear?

A small laboratory for a big question: **can one affine model describe your phone's accelerometer?** A live phyphox viewer pairs the phone's original signal with the same signal after an affine correction, in a parchment-and-brass instrument panel inspired by a scientist turning gears.

**Initial milestone · 20 October 2026.** Report and demo foundations are ready for data collection. No phone measurements, fitted coefficients, empirical improvements, or confirmed failure cases are included yet. The required Python fitting package and analysis are scheduled after collection.

**For teammates and coding agents:** read [AGENTS.md](AGENTS.md) first for the current status, architecture, scientific rules, collaboration workflow, and next milestones.

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

```powershell
npm start -- --phone http://192.168.1.42:8080 --calibration calibration/params.json
```

The address above is an example: substitute the actual URL. An explicit buffer override is available for custom experiments; inspect `/config` first:

```powershell
npm start -- --phone http://192.168.1.42:8080 --buffers acc_time,accX,accY,accZ
```

Other options: `--port 5174`, `--no-open`, `--help`. A **synthetic preview** can exercise the display without a phone. It is labelled throughout, starts only on request, and is never recorded or presented as experimental evidence. Enabling it disconnects the viewer from the phone; it does not stop the phone. Disconnecting or closing this viewer also does not stop a running phyphox experiment.

**Export every experimental recording from phyphox separately.** The viewer holds only 120 s / 30,000 points in memory and never writes into `data/raw/`. Keep the phone awake and phyphox in the foreground. A stale stream, paused experiment, missing buffers and network errors are shown explicitly. A changed experiment session clears the live history and requires reconnection. A bridge restart discards viewer history and any calibration loaded only through the UI.

If connection fails, open the displayed phyphox URL directly in your browser. Check remote access, address, port, same Wi-Fi, VPN settings and guest-network client isolation. The bridge listens on loopback only, so other devices do not need access to the laptop server.

## The model

```text
Measured:     m = S a + b + noise
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
data/raw/               Untouched phone exports (currently empty)
data/processed/         Future rest masks, pose means and derived tables
data/README.md          Collection protocol and pending header/device notes
data/recordings.csv     Metadata table (headers only until collection)
src/calib/              Reserved Python calibration package
calibration/            Identity JSON; future fitted parameters
results/figures/        Future evidence plots
results/metrics/        Future held-out metrics
web/                    Local dashboard HTML, CSS and JavaScript
scripts/                Node live bridge and Windows launcher
tests/                  Live bridge and calibration-application checks
decisions.md            Decisions, alternatives and evidence
```

Read [the report draft](report/report-draft.pdf) or edit [its Markdown source](report/report.md). To rebuild the PDF, optionally install the document-only dependency with `python -m pip install reportlab`, then run `python report/build_report.py`. Python is not required to run the live viewer.

## Verification

```powershell
npm test
npm run check
```

Tests exercise known affine correction, invalid calibration, official phyphox-style buffer discovery, a mock phone with incremental samples, start/stop, reconnect/session handling, event streaming to two windows, bounded client history, spike-preserving trace reduction, signed tilt, the distinction between correction and reference error, and HTTP boundaries. They do not establish the accuracy of a real phone. The course also requires future **pytest** tests of the Python loader, rest detector, and fit/apply class, including parameter recovery from synthetic data; the present Node tests do not replace those.

## Next milestone — after collection

- Record six faces twice, at least four measured ramps, and an independently referenced limit candidate.
- Implement the Python CSV loader and rest detector with at least three meaningful tests.
- Implement the Python `fit(...)` / `apply(...)` class using least squares, with JSON save/load and synthetic parameter-recovery tests.
- Report rank and condition numbers, fit residuals and held-out raw/corrected errors in m/s² and degrees.
- Confirm a failure with evidence and explain whether it belongs to the affine sensor model or the gravity-only interpretation.
- Replace report placeholders with measured results, keep the PDF to 3–4 pages and at most four figures, sign contributions, and rehearse a new live recording.

Commands for these future results will be documented when implemented. There are no working `python -m calib fit` or analysis commands in this milestone.

## References and course logistics

The supplied course PDF, *Sprint project: Is your phone linear?* (18 October 2026), is the requirements source. It is not republished here. It contains conflicting deadline statements: the schedule says 23 October at 12:00; later pages say “Fri 28 Oct, 8:00”. Confirm the deadline and Q&A duration with the course team.

API integration follows the official [phyphox remote-interface reference](https://phyphox.org/docs/remote-interface/) and its [OpenAPI schema](https://phyphox.org/docs/remote-interface/openapi.yaml). The distinction between physical acceleration with gravity and gravity-removed virtual acceleration follows the [phyphox sensor documentation](https://phyphox.org/docs/file-format/input/).
