# Decision log

## 2026-10-23 - Frozen four-height validation and independent typography review
Decision: use the newly supplied 0/4/8/11 cm screen-up runs as a separate validation session with the existing S, b and training-only screening policy, checked by exact hashes. Preserve all input bytes and earlier outcomes; treat camera-supported zero as nominal and also report raised-only sensitivity. Version compact audit/results/figures and leave the new large derived CSV ignored/reproducible. Document the demonstrated static benefit as the report's main result while retaining measured tilt limitations without selective omission.
Alternatives: retrain on the new validation, relabel measured references to match readings, discard the camera-supported zero without disclosure, or replace the earlier experiment silently.
Evidence: 57,686 samples in four 29.76-31.55 s runs; four-run tilt RMSE 3.988562 -> 4.110647 degrees; raised-only 4.604338 -> 4.740403. No parameter or threshold changes. A user-requested independent visual reviewer found that the font embedding regex dropped most KaTeX font-face declarations; preserving CSS declaration boundaries and checking actual loaded fonts fixed all matrices. Final independent inspection passed all four pages with no clipping/collisions.

## 2026-10-23 - Typeset report and preserve measured angle validation
Decision: replace plain-text PDF equation substitution with LaTeX rendered through local KaTeX, embedding fonts/figures into offline HTML and printing the same four-page layout to PDF. Use proper matrix notation, result tables, short paragraphs and readable report-specific plots. Keep document dependencies separate from the runtime viewer; version report sources, lockfile and generated artifacts without changing ignore rules.
Alternatives: retain Python-list coefficients or use runtime CDN fonts/math scripts.
Evidence: the user requested better equation/matrix typography and report aesthetics. Current coefficients and measured results are unchanged. The user confirms the angle geometry and plans four new distinct angles for validation only. Existing adverse angle results remain evidence; neither retraining on them nor silently replacing their references is authorized by that plan.

## 2026-10-23 - Confirmed authorship, shared choices and model presentation
Decision: name Melis Derveni and Harsimranjeet Kaur in report text, PDF author metadata, README and package metadata. Record Melis's measurements/experiments and other deliverables, Harsimranjeet's model training/testing/evaluation, and both authors' joint discussion/agreement on the approach and its tradeoffs. Keep physical signature/date fields blank. Present the fitted model as m = S a + b, with no separate predicted noise term; b remains a constant fitted bias, and validation errors remain measured discrepancies.
Alternatives: leave authorship placeholders, imply isolated responsibility, claim an alternative model was tested when it was only discussed, or introduce an additional fitted error term.
Evidence: the user supplied both full names, contribution allocation and joint decision-making, and requested the simplified equation. The report and separate team-contributions document explain advantages, limitations and reasons for the chosen approach without changing any fitted parameters or validation outcomes.

## 2026-10-23 — Separate analysis, frozen stability policy and honest validation
Decision: preserve the teammate notebook and extend its forward affine regression in separate Python modules. Fit equally weighted static pose means using user-authorized nominal ±g references. Choose a robust 0.25 s local-vector-RMS threshold on static training only, freeze before testing, trim one second at boundaries and retain continuous stable intervals of at least one second. Do not filter by gravity magnitude, target discrepancy or held-out improvement. Use unsigned long-axis angle validation because full signed reference vectors are unspecified. Version compact measured results, four analysis figures and a named fitted JSON; keep large masks ignored/reproducible under existing rules.
Alternatives: edit the notebook, tune on angle errors, infer exact orientations from measured vectors, or omit negative validation results.
Evidence: the full-row notebook result reproduces independently. Screened static vector RMSE is 0.215965 -> 0.111114 m/s²; held-out angle RMSE worsens 3.267287 -> 3.726342 degrees. The static -Z error also worsens slightly. All acquisition hashes and notebook bytes remain unchanged. Tests verify recovery, invalid/deficient inputs, stability/gaps and policy freezing; numerical/browser checks verify exported calibration compatibility. The four-page measured report includes the limitations. No independently referenced affine failure or physical fitted-phone rehearsal is claimed. Ruler/contact uncertainty, case/rate consistency, signatures remain for Melis Derveni and Harsimranjeet Kaur.

## 2026-10-22 — Publish angle datasets
Decision: at the user's explicit request, version all three generated angle datasets (training.csv, testing.csv and limit.csv) alongside the already-published raw export. Add narrowly scoped ignore exceptions and preserve exact bytes in Git so existing audit hashes remain valid. Other generated data stays ignored.
Alternatives: require teammates to regenerate the CSVs from the raw export.
Evidence: the user reports the new data is missing from Git. The raw export was already published on data/angle-preprocessing-2026-10-22, but generated CSVs were ignored. All source/output hashes match the existing audit; publishing adds no new preprocessing or scientific results.

## 2026-10-22 — Angle acquisition and reversible boundary preprocessing
Decision: partition the new export with original START/PAUSE intervals into four consecutive ramp pairs and a ninth shaking run. Preserve training/testing acquisition labels while reserving ramps for validation of the same future static-face affine fit. Retain all rows/numeric strings; flag only the first/last second of quiet intervals as excluded by a fixed timing precaution. Do not smooth, remove shaking peaks, fit parameters or claim a general rest detector. Version compact audit/protocol and trace review; keep new large processed CSVs ignored and reproducible without changing ignore rules.
Alternatives: guess 30-second cuts, tune masks from validation errors, merge angle samples into fitting, fit a second model, or call strong shaking an observed affine failure.
Evidence: 131,834 finite samples in nine 30.001–32.542 s runs. Training/testing/limit counts are 58,204/58,885/14,745; quiet included counts are 54,440/55,122. The user confirms a 16 cm hypotenuse with 10 cm height in runs 1–4 and 5 cm in runs 5–8, giving 38.6822°/18.2100°. First pair at each height is screen-up; second pair is on its side. Raw hashes, exact coverage and per-run variability are audited; original bytes are unchanged. Shaking reaches vector magnitude 119.821 m/s² but lacks an independent force reference. Exact signed vectors and geometry uncertainty remain unspecified. Eight Python tests and 31 Node tests/check pass; the trace/mask SVG was rendered and reviewed.

Each entry records the decision, alternatives, and evidence. Proposed decisions remain revisable after measurements; no empirical benefit is claimed today.

## 2026-10-20 — Scope
Decision: deliver the report draft, directory structure and local live viewer now; collect phone data on 21 October and implement fitting/analysis after that.
Alternatives: implement the entire pipeline today or invent illustrative results.
Evidence: explicit user scope; no phone dataset exists yet.

## 2026-10-20 — Sensor and hypothesis
Decision: use Acceleration with g and test m = S a + b with a full 3×3 S as the planned model.
Alternatives: gravity-removed virtual sensor; diagonal gains only.
Evidence: the supplied brief requires gravity-based calibration and full-model assessment; the full matrix has not yet been shown to outperform the diagonal model.

## 2026-10-20 — Holdout
Decision: reserve repeated session B and independent ramps for final testing; session A supplies fitting and threshold/model choices.
Alternatives: random time-sample split or selecting poses after inspecting test errors.
Evidence: adjacent samples are correlated; the brief requires independent recordings. This split is fixed before collection.

## 2026-10-20 — Honest comparison
Decision: default to an identity transform with explicit uncalibrated labels; allow validated-format JSON uploads and a separate labelled synthetic preview.
Alternatives: fabricated calibration parameters or silently simulated data.
Evidence: no fitted parameters are available. Raw and corrected points are paired at identical timestamps and plotted on shared axes.

## 2026-10-20 — Local demo architecture
Decision: use a Node.js standard-library localhost bridge and buildless canvas frontend; keep the future required Python calibration package separate.
Alternatives: an internet-hosted dashboard reaching a private phone; dependency-heavy frontend and plotting services.
Evidence: the phone exposes its phyphox HTTP API on the local network. A local bridge avoids browser mixed-content restrictions and external runtime assets. Primary API reference: https://phyphox.org/docs/remote-interface/openapi.yaml.

## 2026-10-20 — Limit experiment
Decision: plan stationary drift as the first limit candidate, and require measured evidence before calling any condition a failure.
Alternatives: conclude from shaking that the sensor is non-affine, or assume complete sensor breakdown is necessary.
Evidence: motion changes specific force and confounds gravity-only tilt; the brief asks for an honest model limit, not hardware destruction. Candidate outcome is pending.

## 2026-10-20 — Course date conflict
Decision: record both contradictory deadline statements and confirm them with the course team; plan conservatively around 23 October until clarified.
Alternatives: silently choose a date from the PDF.
Evidence: the week table says Friday 23 October at 12:00; deliverable text says Friday 28 October at 08:00 (28 October 2026 is Wednesday) and gives different question durations.

## 2026-10-20 — Live controls and rendering
Decision: put large Start/Stop controls above both graph views; stream incremental updates over SSE, poll the phone up to 20 times per second, cache calibration/plot work, and preserve per-pixel trace extrema.
Alternatives: sidebar-only controls, repeated full-history downloads, or smoothing measured values to hide roughness.
Evidence: the display window hid the sidebar; a live session returned about 1.66 MB per full-history request. Browser QA with a 500 Hz mock phone passed both-window controls and rendering; mathematical samples remain unchanged. This improves the demo transport/display, not the scientific calibration.

## 2026-10-20 — Presentation and reference errors
Decision: add paired inclination dials and one focused comparison panel above an expandable original trace inspector. Separate applied correction from error against an independent reference; start reference comparisons only with fresh samples after explicit still-phone confirmation.
Alternatives: six simultaneous axis plots, exaggerating the corrected physical scale, or reporting a change in reading as an accuracy improvement.
Evidence: the user found three overlaid axes hard to read and expected a small real correction. Unit/browser checks verify identity gives no improvement, references do not label earlier motion, negative reductions remain negative, and calibration changes invalidate the confirmed period. All experimental benefit remains unmeasured.

## 2026-10-21 — Live 3D phone and motion limits
Decision: add a locally authored S25 Ultra at Samsung's published body proportions, a fixed transparent plane, quaternion interpolation, gravity-only tilt, and an optional OS-fused attitude stream using an independent time buffer. Do not simulate a failure or extra lag when shaken.
Alternatives: infer unobservable heading/position from acceleration, deliberately slow the model during shaking, or present tracker/display limitations as proof the affine sensor model failed.
Evidence: the user requested a realistic moving phone and a shaking demonstration. Accelerometer-only data cannot separate arbitrary motion from gravity or determine heading; phyphox attitude supplies a separate fused estimate (official input documentation). Mock/browser tests cover pose changes, strong-motion labels, fused yaw, stale data and mobile rendering. Physical validation of the optional configuration and scientific model-failure evidence remain pending. Sources: https://phyphox.org/docs/file-format/input/ and https://www.samsung.com/ca/smartphones/galaxy-s25-ultra/specs/.

## 2026-10-21 — First static export and complete-repeat split
Decision: use the original phyphox START/PAUSE event log to partition all twelve acquisition runs. First of each consecutive pose pair trains; second tests. Keep every row and original numeric string, with source-row/run/split provenance. Version the script and compact audit; leave large derived CSVs ignored and reproducible. Do not fit, trim or resample at this stage.
Alternatives: guess 30-second boundaries, randomly distribute correlated rows, call same-session repeats independent sessions, or infer true reference vectors from measured acceleration.
Evidence: 172,447 finite rows; twelve event intervals of 29.34–32.06 s; measured pairs +Y, -Y, -X, +X, +Z, -Z. Training/testing counts are 86,323/86,124 with complete coverage and no overlap. The user's corrected intended pose list includes all six signed axes. Source SHA-256 and exact boundaries are recorded in `data/splits/static-2026-10-21/manifest.json`; five split tests verify preservation, boundaries, invalid input and repeat structure. One collection session limits independence; ramps, reference alignment, case/settings and rest masks remain pending.

## 2026-10-21 — Smoother orientation and explicit full-rotation setup
Decision: interpolate timestamped measured poses using a fixed 70 ms display buffer instead of easing toward only the last sample of each network delivery. Retain bounded intermediate attitude poses on their own clock. Continue gravity-based poses from their preceding orientation to avoid screen-down heading discontinuities; heading remains unobserved. Show explicit full-rotation setup when attitude is absent.
Alternatives: increase smoothing lag, manufacture missing yaw from acceleration, extrapolate unmeasured poses, or silently alter the active phone experiment.
Evidence: the live `/config` exposed only physical acceleration when the user reported rough two-axis tracking and a missing third rotation. Pure tests cover screen-down continuity, both observable complete rotations, buffered timing, endpoint clamping and duplicate arrivals; integration verifies attitude batch retention/reset. Browser checks with a separate 500 Hz mock phone verify model transforms, fused yaw, stale/paused states and mobile layout with no JavaScript exceptions. The physical combined experiment still needs import/verification. Source: https://phyphox.org/docs/file-format/input/.

## 2026-10-21 — Full-orientation import and long-recording reconnect
Decision: supply a static offline QR containing the combined experiment ZIP using phyphox's documented header/CRC32 format. Make the required phone-side import steps explicit. Bootstrap live connections from single latest timestamps and bounded recent windows, leaving the phone archive untouched.
Alternatives: require internet hosting for experiment import, expose the localhost bridge on the LAN, pretend smoothing can recover heading, or clear a long recording to make reconnect work.
Evidence: the user needs accurate full rotation; the active phone experiment exposes acceleration only. Restarting the bridge revealed an oversized full-history response. The new bootstrap has an integration test and the browser mock checks pass; the generator verifies its payload and ZIP round-trip. Physical QR import/full orientation still needs verification. Official formats: https://phyphox.org/docs/transferring-experiments/ and https://phyphox.org/docs/remote-interface/.

## 2026-10-21 — Explicit motion pause requested by the user
Decision: retain normal tracking during gentle movement, but hold the displayed pose with a red warning on strong acceleration or quaternion-derived speed above 240°/s (0.15 s window). Resume after 0.6 s of measured quiet time, with a 180 ms return blend. Mark it as an intentional display policy; fused attitude may still be accurate. Acquisition and graphs continue. The pulse is confined to one symbol at less than 1 Hz and respects reduced-motion settings.
Alternatives: fabricate a sensor failure, present a UI hold as empirical affine-model breakdown, or continue tracking without the requested warning/hold.
Evidence: the user reports that the phone now follows closely and explicitly requests stopping the model during fast motion. The thresholds are presentation heuristics, not measured performance limits. Three added tests check angular speed, quiet-time hysteresis, duplicate timestamps, missing/stale data and gravity-only recovery. Physical thresholds still need rehearsal; this change is not calibration evidence.

## 2026-10-21 — More permissive motion pause and faster recovery
Decision: at the user's request, raise the pause limits to current vector magnitude above 40 m/s² or angular speed above 720°/s. Remove the lower uncertainty-badge thresholds from the pause decision. Resume after 0.15 s below 30 m/s² and 180°/s, with an 80 ms return blend.
Alternatives: retain the overly sensitive 1.5 m/s² deviation/variation trigger, or require complete stillness before resuming.
Evidence: the user reports excessive freezing and specifically suggests magnitude above 40 and faster recovery. Updated tests check exact limits, continued tracking during vigorous motion, hysteresis, and prompt recovery while some movement remains. These remain presentation settings, not measured sensor-failure limits.

## 2026-10-21 — Stronger signal required for the motion pause
Decision: raise the vector-magnitude trigger from 40 to 60 m/s². Keep rotation at 720°/s and recovery at 0.15 s plus the 80 ms blend. No additional trigger delay is introduced.
Alternatives: add a grace-period timer instead of increasing the required signal strength.
Evidence: the user clarified that stronger signals should start the freeze and suggested 60. Tests cover continued tracking at 50 and exactly 60 m/s², plus triggering above 60 m/s². This remains a display threshold, not a measured sensor limit.

## 2026-10-21 — Publish both dataset splits
Decision: publish the original export and both generated static training/testing CSVs, together with the split script and audit. Add narrowly scoped ignore exceptions and disable Git text conversion for the two split CSVs so recorded hashes survive checkout on other systems. Other generated artifacts remain ignored.
Alternatives: publish only the raw export and require teammates to regenerate the split CSVs.
Evidence: the user explicitly requested pushing the datasets as well as the project changes. The manifest verifies source/output hashes and records complete, disjoint assignment of all 172,447 samples.
