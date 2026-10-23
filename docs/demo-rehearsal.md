# Demo rehearsal with the measured calibration

From the repository root, with Node 22 or newer:

```powershell
npm.cmd start -- --calibration calibration/fit-static-2026-10-21.json
```

Use `npm start` on systems without the PowerShell launcher restriction. No Python dependencies are needed to run the viewer. It starts locally, with the measured static fit loaded and its name/provenance available. Starting without the calibration option deliberately keeps identity/uncalibrated as the default. The UI's **Load calibration** button accepts the same file. Reset returns both windows to identity.

1. Open phyphox **Acceleration with g**, enable remote access, and connect the displayed private address. This connects without starting, clearing or stopping acquisition. Export recordings separately; the viewer is not an archive.
2. Confirm **Fitted calibration · verify on held-out data**. Fitted means derived from training, not universally validated. The static nominal-reference vector RMSE improved, but the held-out angle RMSE worsened. Say this clearly during the presentation.
3. Select **Display window** and move it to the presentation screen. Start/Stop stay above the graphs. All windows use the same samples, calibration, time limits and scales. Use raw/corrected signal view to compare measurements; correction alone is not error reduction.
4. For a stationary reference comparison, choose the long phone Y direction, enter the independently measured **signed** slope matching that orientation, and confirm the still-phone checkbox. Confirm before starting a fresh stationary period. Unsigned offline validation uses the magnitude of Y inclination; the live dial is signed. Moving or changing reference invalidates confirmation. Show positive or negative current-sample error reduction honestly; it is not held-out RMSE.
5. For a 3D full-rotation demonstration, export existing data before importing the optional combined motion experiment. The offline setup QR is in the motion section. Enable remote access in that experiment and reconnect. Fused attitude is the phone's estimate, not independent truth. This optional demo experiment requests different rates from the scientific static/ramp exports.
6. If demonstrating shaking, explain that acceleration no longer represents gravity alone. The red hold is a deliberate display policy at strong motion, while acquisition/graphs continue. Do not call that warning an observed affine sensor failure.
7. Stop the phone explicitly and export any new scientific recording. Closing/disconnecting the viewer does not stop phone acquisition.

Without a phone, **Synthetic preview** exercises both windows and remains visibly labelled. It never substitutes for physical evidence. CLI calibration loading, file upload/reset, synchronized windows, synthetic correction values, mobile layout and visible controls were checked in real headless Edge. Physical rehearsal of this fitted artifact is still required.

## What the authors still need to supply

- Signatures and date from Melis Derveni and Harsimranjeet Kaur; their names and contributions are recorded in the report.
- Ruler resolution/contact uncertainty for the 5 cm, 10 cm and 16 cm geometry; consistent case configuration and selected sampling setting. The dimensions themselves are confirmed.
- A final phone-connected rehearsal and confirmation that the physical supported angles match the contact geometry.
- Within-height repeats if estimating angle repeatability, and an independently referenced experiment if claiming actual affine-model failure. Existing results remain in the report.
- The course team's resolution of the contradictory deadline and Q&A instructions.

## New angle-validation session: collected 23 October

The new raw export contains four screen-up runs at actual heights 0, 4, 8 and 11 cm, with the same 16 cm hypotenuse. It has been evaluated against the unchanged six-position model. Run `python scripts/validate_new_angles.py`; see `results/angle-validation-2026-10-23/README.md` for the measured references and raw/corrected results. Zero height rests on camera bumps and is nominal rather than independently levelled.

These are validation recordings, not fitting data. The earlier eight-run angle experiment remains separate evidence. Future repeats or new training require explicit roles; do not optimise the current calibration using these held-out angle errors.
