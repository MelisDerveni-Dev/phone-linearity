"""Evaluate the new four-height export with the existing frozen static fit.

Raw CSV/event readers are shared with the acquisition splitter. Every original
row/string survives in a separate derived CSV; preprocessing never selects by
reference error. Earlier angle results and fitted artifacts are read-only.
"""
import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from split_static_recording import HEADERS, ROOT, display_path, partition, read_intervals, read_samples, sha256
from calib import AffineCalibration
from calib.analysis import csv_file, json_file, slope_degrees
from calib.data import Recording, screen


def evaluate(source, protocol_path, calibration_path, policy_path, output, audit, processed):
    source, protocol_path, calibration_path, policy_path, output, audit, processed = [
        Path(p).resolve() for p in (source, protocol_path, calibration_path, policy_path, output, audit, processed)]
    for target in (output, audit, processed):
        if target == source or target.is_relative_to(source) or target.is_relative_to(ROOT / "data/raw"):
            raise ValueError("Derived outputs must stay outside raw data")
    for i, target in enumerate((output, audit, processed)):
        for other in (output, audit, processed)[i+1:]:
            if target == other or target.is_relative_to(other) or other.is_relative_to(target):
                raise ValueError("Use separate result, audit and processed directories")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if sha256(calibration_path) != protocol["calibration_sha256"]:
        raise ValueError("Frozen calibration hash differs from the recorded validation input")
    if sha256(policy_path) != protocol["frozen_policy_sha256"]:
        raise ValueError("Frozen preprocessing policy hash differs from the recorded input")
    model = AffineCalibration.load(calibration_path)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    threshold = float(policy["stability_threshold_m_s2"])
    if threshold != model.provenance["stability_threshold_m_s2"]:
        raise ValueError("Calibration and frozen policy stability thresholds differ")
    inputs = [source / "Raw Data.csv", source / "meta/time.csv", source / "meta/device.csv",
              protocol_path, calibration_path, policy_path]
    hashes = {display_path(p): sha256(p) for p in inputs}
    intervals = read_intervals(source / "meta/time.csv")
    rows, samples = read_samples(source / "Raw Data.csv")
    heights = protocol["height_order_m"]
    length = float(protocol["contact_spacing_m"])
    if len(intervals) != len(heights) or len(heights) != 4:
        raise ValueError("Expected exactly four complete runs and four specified heights")
    if not math.isfinite(length) or length <= 0 or any(not math.isfinite(h) or not 0 <= h <= length for h in heights):
        raise ValueError("Invalid finite height/hypotenuse geometry")
    groups = partition(samples, intervals)
    segment = np.empty(len(rows), dtype=int)
    references = np.empty(len(rows))
    row_heights = np.empty(len(rows))
    for interval, ids, h in zip(intervals, groups, heights):
        segment[ids] = interval["segment_id"]
        references[ids] = math.degrees(math.asin(h / length))
        row_heights[ids] = h
    array = np.asarray(samples)
    rec = Recording([{"split": "validation", "source_row": i+1} for i in range(len(rows))],
                    array[:, 0], array[:, 1:4], segment)
    mask, variation, boundary, _ = screen(rec, {s["segment_id"]: s for s in intervals}, threshold)
    metrics, segments = [], []
    for interval, ids, height in zip(intervals, groups, heights):
        selected = np.asarray(ids)[mask[ids]]
        if not len(selected):
            raise ValueError(f"No stable samples in run {interval['segment_id']}")
        mean = rec.xyz[selected].mean(axis=0)
        corrected = model.apply(mean)
        reference = references[ids[0]]
        row = {"segment_id": interval["segment_id"], "height_m": height,
               "contact_spacing_m": length, "reference_angle_deg": float(reference),
               "reference_status": "nominal table rest; camera bumps" if height == 0 else "user-measured wall geometry",
               "total_samples": len(ids), "included_samples": len(selected)}
        for name, vector in (("raw", mean), ("corrected", corrected)):
            angle = float(slope_degrees(vector))
            row[name+"_angle_deg"] = angle
            row[name+"_signed_error_deg"] = angle-reference
            row[name+"_absolute_error_deg"] = abs(angle-reference)
        metrics.append(row)
        segments.append({**interval, **row, "first_source_row": ids[0]+1, "last_source_row": ids[-1]+1,
            "mean_xyz_m_s2": mean.tolist(), "std_xyz_m_s2": rec.xyz[selected].std(axis=0).tolist(),
            "boundary_excluded_samples": int((~boundary[ids]).sum()),
            "interior_excluded_samples": int((boundary[ids] & ~mask[ids]).sum())})
    # Every validation input remains read-only; outputs are created after checks.
    for target in (output, audit, processed):
        target.mkdir(parents=True, exist_ok=True)
    csv_path = processed / "validation.csv"
    extra = ["source_row", "segment_id", "split", "support_orientation", "height_m", "contact_spacing_m",
             "angle_deg", "include", "exclusion_reason", "rms_variation_m_s2"]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(HEADERS + extra)
        for i, row in enumerate(rows):
            writer.writerow(row + [i+1, int(segment[i]), "validation", protocol["support_orientation"],
                row_heights[i], length, references[i], int(mask[i]),
                "" if mask[i] else "boundary" if not boundary[i] else "variation_gap_or_short_interval",
                float(variation[i]) if np.isfinite(variation[i]) else ""])
    csv_file(output / "angle-validation.csv", metrics)
    csv_file(audit / "segments.csv", [{key: value for key, value in s.items()
        if not isinstance(value, list)} for s in segments])
    summary = {"aggregation": "Four run means, equal weight; same samples for raw/corrected; model and policy frozen.",
        "raised_only_note": "Three nonzero heights, reported separately because table rest includes camera bumps."}
    for name in ("raw", "corrected"):
        errors = np.array([row[name+"_signed_error_deg"] for row in metrics])
        summary[name+"_tilt_rmse_deg"] = float(np.sqrt(np.mean(errors**2)))
        summary[name+"_raised_only_tilt_rmse_deg"] = float(np.sqrt(np.mean(errors[np.array(heights)>0]**2)))
    report = {"schema_version": 1, "protocol": protocol, "input_sha256": hashes,
        "frozen_stability_threshold_m_s2": threshold, "samples": len(rows), "included_samples": int(mask.sum()),
        "summary": summary, "segments": segments,
        "derived_csv": {"path": display_path(csv_path), "sha256": sha256(csv_path)},
        "limitations": ["The zero-height run rests on camera bumps; actual body level is not independently established.",
            "Each of four distinct heights has one acquisition; repeatability is not quantified within this new session.",
            "Measurement precision and case/rate consistency remain unspecified; reference values are retained as supplied.",
            "No retraining or threshold tuning; previous angle validation remains a separate recorded experiment.",
            "A worse tilt result is not uniquely attributed to sensor nonlinearity or reference error."]}
    if any(sha256(p) != hashes[display_path(p)] for p in inputs):
        raise RuntimeError("A validation input changed during evaluation")
    json_file(audit / "manifest.json", report)
    json_file(output / "metrics.json", report)
    plot_validation(output, rec, mask, variation, threshold, groups, metrics)
    lines = ["# Four-height validation: 23 October 2026", "",
        "Frozen six-position calibration; no angle fitting or policy changes. All raw rows remain unchanged. Reproduce with `python scripts/validate_new_angles.py`.", "",
        "| Height (cm) | Reference (°) | Raw (°) | Corrected (°) | Raw absolute error (°) | Corrected absolute error (°) |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in metrics:
        lines.append(f"| {row['height_m']*100:.0f} | {row['reference_angle_deg']:.4f} | {row['raw_angle_deg']:.4f} | {row['corrected_angle_deg']:.4f} | {row['raw_absolute_error_deg']:.4f} | {row['corrected_absolute_error_deg']:.4f} |")
    lines += ["", f"All four run means: **{summary['raw_tilt_rmse_deg']:.6f} -> {summary['corrected_tilt_rmse_deg']:.6f} degrees RMSE**.", "",
        f"Raised-only sensitivity (three run means): **{summary['raw_raised_only_tilt_rmse_deg']:.6f} -> {summary['corrected_raised_only_tilt_rmse_deg']:.6f} degrees RMSE**. This is a labelled subset, not a replacement headline or tuned selection.", "",
        f"{len(rows):,} samples; {int(mask.sum()):,} included by the frozen 0.25 s RMS / 1 s boundary and duration policy. See manifest for exclusion counts and exact [START, PAUSE) intervals. The derived per-sample CSV is ignored and reproducible; compact audit/results and figures are shareable.", "",
        *["- "+note for note in report["limitations"]], ""]
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")
    (audit / "README.md").write_text("# Acquisition audit: four heights\n\nSee [results](../../../results/angle-validation-2026-10-23/README.md). `manifest.json` preserves input hashes, full row coverage, frozen calibration/policy hashes and exact boundaries. Heights follow the user's acquisition order.\n", encoding="utf-8")
    return report


def plot_validation(output, rec, mask, variation, threshold, groups, metrics):
    fig, axes = plt.subplots(2, 1, figsize=(10, 7))
    x = np.arange(4)
    for name, offset in (("raw", -.18), ("corrected", .18)):
        axes[0].bar(x+offset, [r[name+"_absolute_error_deg"] for r in metrics], .36, label=name)
        axes[1].plot([r["reference_angle_deg"] for r in metrics], [r[name+"_angle_deg"] for r in metrics], "o-", label=name)
    axes[0].set_xticks(x, [f"{r['height_m']*100:.0f} cm" for r in metrics])
    axes[0].set_ylabel("Absolute tilt error (degrees)")
    axes[1].plot([0,45],[0,45], "k--", label="reference agreement")
    axes[1].set(xlabel="Geometry reference (degrees)", ylabel="Measured tilt (degrees)")
    for ax in axes:
        ax.legend()
    fig.suptitle("New screen-up session: frozen model; nominal 0° rests on camera bumps")
    fig.tight_layout()
    fig.savefig(output / "angle-validation.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(4, 1, figsize=(10, 8))
    for ax, ids, row in zip(axes, groups, metrics):
        t = rec.t[ids]-rec.t[ids][0]
        ax.plot(t, np.minimum(variation[ids], threshold*3), lw=.7)
        ax.fill_between(t, 0, threshold*3, where=~mask[ids], alpha=.25, color="grey")
        ax.axhline(threshold, ls="--", color="coral")
        ax.set_title(f"{row['height_m']*100:.0f} cm: {row['included_samples']}/{row['total_samples']} included", fontsize=10)
        ax.set_ylabel("RMS (m/s²)")
        ax.set_ylim(0,threshold*3)
    axes[-1].set_xlabel("Time within run (s)")
    fig.suptitle("Frozen stability masks; grey excluded; display capped at 3 x threshold")
    fig.tight_layout()
    fig.savefig(output / "stability-masks.png", dpi=140)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", nargs="?", type=Path, default=ROOT / "data/raw/Acceleration with g 2026-10-23 11-40-57")
    args = parser.parse_args()
    result = evaluate(args.source_dir, ROOT / "data/splits/angles-2026-10-23/protocol.json",
        ROOT / "calibration/fit-static-2026-10-21.json", ROOT / "results/analysis-2026-10-23/frozen-policy.json",
        ROOT / "results/angle-validation-2026-10-23", ROOT / "data/splits/angles-2026-10-23",
        ROOT / "data/processed/angles-2026-10-23")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
