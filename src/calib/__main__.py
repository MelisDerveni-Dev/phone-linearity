"""Command line: python -m calib {fit,apply,analyse,evidence}.

  fit       fit S and b on the static training repeats and save JSON
  apply     correct a new phyphox export with a saved calibration
  analyse   reproduce the frozen fit, stability policy and held-out metrics
  evidence  model comparison, linearity test, repeatability and limits
"""
import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

from .analysis import G, POSES, ROOT, interval_map, pose_means, slope_degrees
from .data import load_csv, read_export, screen
from .model import AffineCalibration


def fit_command(args):
    training = load_csv(args.training)
    mask, _, _, threshold = screen(training, interval_map(args.manifest))
    model = AffineCalibration.fit(np.array(list(POSES.values())), pose_means(training, mask), {
        "training_session": "static-2026-10-21 / first within-session repeats", "files": [str(args.training)],
        "stability_threshold_m_s2": threshold, "gravity_m_s2": G,
        "method": f"Equal-weight pose means; {args.model} least squares."},
        structure="diagonal" if args.model == "six-position" else "full",
        name=f"S25 Ultra / {args.model} fit")
    model.save(args.out)
    print(json.dumps({"out": str(args.out), "S": model.S.tolist(), "b": model.b.tolist(), "diagnostics": model.diagnostics}, indent=2))


def apply_command(args):
    source, out = args.export.resolve(), args.out.resolve()
    if out.is_relative_to(ROOT / "data/raw") or out.is_relative_to(source):
        raise SystemExit("Write corrected output outside data/raw and the source export")
    model = AffineCalibration.load(args.calibration)
    recording, intervals = read_export(source)
    corrected = model.apply(recording.xyz)
    raw_tilt, corrected_tilt = slope_degrees(recording.xyz), slope_degrees(corrected)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source_row", "segment_id", "Time (s)", "raw_x", "raw_y", "raw_z", "corrected_x", "corrected_y", "corrected_z",
                         "raw_magnitude", "corrected_magnitude", "raw_long_axis_tilt_deg", "corrected_long_axis_tilt_deg"])
        for i in range(len(recording.t)):
            writer.writerow([i + 1, int(recording.segment[i]), repr(recording.t[i]), *map(repr, recording.xyz[i]), *map(repr, corrected[i]),
                             repr(np.linalg.norm(recording.xyz[i])), repr(np.linalg.norm(corrected[i])),
                             repr(raw_tilt[i]), repr(corrected_tilt[i])])
    summary = []
    for seg in sorted(intervals):
        ids = recording.segment == seg
        still = ids & (np.abs(np.linalg.norm(corrected, axis=1) - G) <= .35)
        row = {"run": seg, "samples": int(ids.sum()), "still_fraction": float(still.sum() / ids.sum())}
        if still.any():
            raw_mean, corrected_mean = recording.xyz[still].mean(axis=0), corrected[still].mean(axis=0)
            row.update(raw_long_axis_tilt_deg=float(slope_degrees(raw_mean)), corrected_long_axis_tilt_deg=float(slope_degrees(corrected_mean)),
                       raw_magnitude_error_m_s2=float(np.linalg.norm(raw_mean) - G), corrected_magnitude_error_m_s2=float(np.linalg.norm(corrected_mean) - G))
        summary.append(row)
    print(json.dumps({"calibration": model.name, "fitted": model.fitted, "out": str(out), "runs": summary,
                      "note": "Run means use samples with |a_hat| within 0.35 m/s^2 of g; tilt assumes a still phone."}, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m calib", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    fit = commands.add_parser("fit", help="fit S and b on the static training repeats")
    fit.add_argument("--model", choices=["full", "six-position"], default="full")
    fit.add_argument("--training", type=Path, default=ROOT / "data/processed/static-2026-10-21/training.csv")
    fit.add_argument("--manifest", type=Path, default=ROOT / "data/splits/static-2026-10-21/manifest.json")
    fit.add_argument("--out", type=Path, default=ROOT / "calibration/params.json")
    apply = commands.add_parser("apply", help="correct a phyphox export (folder with Raw Data.csv and meta/time.csv)")
    apply.add_argument("calibration", type=Path)
    apply.add_argument("export", type=Path)
    apply.add_argument("--out", type=Path, default=ROOT / "results/applied/corrected.csv")
    for name in ("analyse", "evidence"):
        sub = commands.add_parser(name, help="reproduce held-out metrics" if name == "analyse" else "five-question evidence and figures")
        sub.add_argument("--root", type=Path, default=ROOT)
        if name == "analyse":
            sub.add_argument("--refreeze", action="store_true", help="deliberately replace the archived fit and policy")
    args = parser.parse_args(argv)
    if args.command == "fit":
        fit_command(args)
    elif args.command == "apply":
        apply_command(args)
    elif args.command == "analyse":
        from .analysis import run
        run(args.root, args.refreeze)
    else:
        from .evidence import run
        run(args.root)


if __name__ == "__main__":
    sys.exit(main())
