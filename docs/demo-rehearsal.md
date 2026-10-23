# Demo rehearsal with the measured calibration

The brief asks for a live demo on a recording made in the room. Our demo is a **digital spirit level checked against a ruler**, using Harsimranjeet's fitted model (`calibration/fit-static-2026-10-21.json`). The live recording is a fresh test that the model has never seen.

## Start

From the repository root, with Node 22 or newer:

```powershell
npm.cmd start -- --calibration calibration/fit-static-2026-10-21.json
```

Use `npm start` outside the Windows PowerShell launcher restriction. No Python is needed for the viewer. Without `--calibration` the viewer stays on identity, labelled *uncalibrated*. **Load calibration** accepts the same file; Reset returns all windows to identity.

## Script (about 4 minutes)

1. In phyphox open **Acceleration with g**, enable remote access, and connect to the displayed private address. Connecting does not start, clear or stop acquisition. Select **Display window** for the projector.
2. Confirm the badge reads **Fitted calibration**. Fitted means derived from training data, not universally validated.
3. **Level check.** Lay the phone screen-up on the table and press Start. Point out that raw and corrected graphs share time limits and scales. The correction is small: offsets of up to 0.1 m/s², about half a degree of tilt near level.
4. **Ruler check.** Raise one end by a measured height h with contact spacing L. Enter asin(h/L) in degrees for **Along phone Y**, keep the phone still, then tick **Phone held still at this reference**. Show the raw and corrected error on the dials.
   - Say honestly what to expect. In our recordings, the phone reads 3–6° below the ruler angle, repeatably, and calibration moves it by less than 1°. A difference here comes from how the phone rests, not from the sensor (report, Section 4).
5. **Linearity in one sentence.** While the phone is still, the size of the calibrated reading stays within about 0.07 m/s² of 9.81 at any angle. That is the linearity test from the report (question 2).
6. **Where it breaks.** Shake the phone. |m| leaves g by tens of m/s² and the motion badge reports tilt uncertainty. Above 60 m/s² the 3D view holds deliberately, with a red warning. That is the gravity-only model failing (question 5), not a sensor failure, and acquisition continues.
7. Stop the phone explicitly and export the recording from phyphox. Closing the viewer does not stop acquisition.

## Offline backup

If the network fails, record the same steps in phyphox, export the folder, and run:

```powershell
python -m calib apply calibration/fit-static-2026-10-21.json "<export folder>" --out results/applied/demo.csv
```

It prints, per START/PAUSE run, the raw and corrected long-axis tilt and |â| − g for samples within 0.35 m/s² of g.

Without a phone, **Synthetic preview** exercises both windows and stays visibly labelled. It is never evidence.

## Still to do before the presentation

- A physical rehearsal with the fitted JSON, including the separate display window. Browser checks used mock data only.
- Signatures and date on the report from Melis Derveni and Harsimranjeet Kaur.
- Confirming the deadline with the course team: the brief gives both 23 October 12:00 and "Fri 28 Oct, 8:00".
- Each presenter should be ready to explain three things: why six poses are needed (rank 4), why a still phone reading 9.81 at every angle tests linearity without a ruler, and why shaking breaks the model without proving the sensor itself is nonlinear.
