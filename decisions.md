# Decision log

Each entry records the decision, alternatives, and evidence. Proposed decisions remain revisable after measurements; no empirical benefit is claimed today.

## 2026-10-20 — Scope
Decision: deliver the report draft, directory structure and local live viewer now; collect phone data on 21 October and implement fitting/analysis after that.
Alternatives: implement the entire pipeline today or invent illustrative results.
Evidence: explicit user scope; no phone dataset exists yet.

## 2026-10-20 — Sensor and hypothesis
Decision: use Acceleration with g and test m = S a + b + noise with a full 3×3 S as the planned model.
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
