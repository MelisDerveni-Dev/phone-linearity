"""Reproduce notebook regression, freeze training choices, validate, and export."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data import load_csv, screen
from .model import AffineCalibration

ROOT = Path(__file__).resolve().parents[2]
G = 9.81
POSES = {"+X": [G, 0, 0], "-X": [-G, 0, 0], "+Y": [0, G, 0],
         "-Y": [0, -G, 0], "+Z": [0, 0, G], "-Z": [0, 0, -G]}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_file(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def csv_file(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def interval_map(path):
    return {int(s["segment_id"]): s for s in json.loads(path.read_text(encoding="utf-8"))["segments"]}


def pose_means(recording, mask):
    result = []
    for pose in POSES:
        ids = mask & np.array([r.get("pose_observed") == pose for r in recording.rows])
        if ids.sum() < 2:
            raise ValueError(f"No usable samples for {pose}")
        result.append(recording.xyz[ids].mean(axis=0))
    return np.array(result)


def static_metrics(means, model):
    reference = np.array(list(POSES.values()))
    corrected = model.apply(means)
    rows = []
    for pose, ref, raw, corr in zip(POSES, reference, means, corrected):
        row = {"pose": pose}
        for name, value in (("raw", raw), ("corrected", corr)):
            row[name + "_vector_error_m_s2"] = float(np.linalg.norm(value - ref))
            row[name + "_magnitude_error_m_s2"] = float(abs(np.linalg.norm(value) - G))
            cosine = np.dot(value, ref) / (np.linalg.norm(value) * G)
            row[name + "_direction_error_deg"] = float(np.degrees(np.arccos(np.clip(cosine, -1, 1))))
        rows.append(row)
    summary = {"aggregation": "Six pose means, equal weight; not sample RMSE or independent-session accuracy."}
    for name in ("raw", "corrected"):
        for kind, unit in (("vector", "m_s2"), ("magnitude", "m_s2"), ("direction", "deg")):
            values = np.array([r[f"{name}_{kind}_error_{unit}"] for r in rows])
            summary[f"{name}_{kind}_rmse_{unit}"] = float(np.sqrt(np.mean(values ** 2)))
            summary[f"{name}_{kind}_mean_error_{unit}"] = float(np.mean(values))
    return rows, summary


def slope_degrees(values):
    """Unsigned inclination of the phone's long (+/-Y) axis to horizontal.

    Works for both screen-up and on-side support. No unconfirmed full reference
    vector or signed tilt is assigned from measured components.
    """
    values = np.asarray(values)
    return np.degrees(np.arctan2(np.abs(values[..., 1]), np.hypot(values[..., 0], values[..., 2])))


def save_masks(name, rec, include, variation, boundary, masks):
    csv_file(masks / f"{name}.csv", [{"source_row": r["source_row"], "segment_id": int(seg),
        "include": int(keep), "boundary_eligible": int(edge),
        "rms_variation_m_s2": float(v) if np.isfinite(v) else "",
        "exclusion_reason": "" if keep else "boundary" if not edge else "variation_gap_or_short_interval"}
        for r, seg, keep, v, edge in zip(rec.rows, rec.segment, include, variation, boundary)])


def run(root=ROOT):
    root = Path(root)
    output = root / "results/analysis-2026-10-23"
    masks = root / "data/processed/analysis-2026-10-23"
    output.mkdir(parents=True, exist_ok=True)
    masks.mkdir(parents=True, exist_ok=True)
    static_dir = root / "data/processed/static-2026-10-21"
    angle_dir = root / "data/processed/angles-2026-10-22"
    sources = {}
    # Verify the original acquisition artifacts rather than silently using edited data.
    for folder in ("static-2026-10-21", "angles-2026-10-22"):
        audit = root / "data/splits" / folder / "manifest.json"
        manifest = json.loads(audit.read_text(encoding="utf-8"))
        for path, expected in manifest["source_sha256"].items():
            if digest(root / path) != expected:
                raise ValueError(f"Acquisition source hash changed: {path}")
            sources[path] = expected
        for info in manifest["outputs"].values():
            if digest(root / info["path"]) != info["sha256"]:
                raise ValueError(f"Processed acquisition hash changed: {info['path']}")
            sources[info["path"]] = info["sha256"]
    notebook_hashes = {p.name: digest(p) for p in root.glob("*.ipynb")}
    static_intervals = interval_map(root / "data/splits/static-2026-10-21/manifest.json")
    train = load_csv(static_dir / "training.csv")
    train_mask, train_var, train_edge, threshold = screen(train, static_intervals)
    provenance = {"training_session": "static-2026-10-21 / first within-session repeats",
                  "files": ["data/processed/static-2026-10-21/training.csv"],
                  "training_sha256": digest(static_dir / "training.csv"),
                  "reference": "Nominal six +/-9.81 m/s^2 axes; placement uncertainty includes rear cameras and side buttons.",
                  "method": "Equal-weight pose means; forward least squares via NumPy SVD; notebook regression retained.",
                  "gravity_m_s2": G, "stability_threshold_m_s2": threshold,
                  "stability_policy": "0.25 s local vector RMS; threshold=max(0.05,training median+8*1.4826*MAD); 1 s boundary trim, 1 s minimum interval; gaps >0.1 s break continuity."}
    model = AffineCalibration.fit(np.array(list(POSES.values())), pose_means(train, train_mask), provenance)
    calibration_path = root / "calibration/fit-static-2026-10-21.json"
    model.save(calibration_path)
    json_file(output / "frozen-policy.json", {**provenance, "diagnostics": model.diagnostics,
        "selection": "Frozen from training before loading test/angle samples; not tuned for held-out improvement."})
    save_masks("static-training-mask", train, train_mask, train_var, train_edge, masks)
    # Nothing below this point changes the model or stability policy.
    test = load_csv(static_dir / "testing.csv")
    if {r["split"] for r in test.rows} != {"testing"}:
        raise ValueError("Expected held-out static testing labels")
    if {r["source_row"] for r in train.rows} & {r["source_row"] for r in test.rows}:
        raise ValueError("Training/testing source-row overlap")
    test_mask, test_var, test_edge, _ = screen(test, static_intervals, threshold)
    save_masks("static-testing-mask", test, test_mask, test_var, test_edge, masks)
    rows, summary = static_metrics(pose_means(test, test_mask), model)
    csv_file(output / "static-test.csv", rows)
    baseline = AffineCalibration.fit(np.array(list(POSES.values())), pose_means(train, np.ones(len(train.t), bool)),
                                     {"method": "Notebook reproduction only; not the exported fit"})
    _, baseline_summary = static_metrics(pose_means(test, np.ones(len(test.t), bool)), baseline)
    summaries = []
    for split, rec, mask in (("training", train, train_mask), ("testing", test, test_mask)):
        for seg in np.unique(rec.segment):
            all_ids = rec.segment == seg
            ids = all_ids & mask
            if not ids.any():
                raise ValueError(f"No stable samples in static segment {seg}")
            mean, std = rec.xyz[ids].mean(axis=0), rec.xyz[ids].std(axis=0)
            summaries.append({"split": split, "segment_id": int(seg),
                "pose": rec.rows[np.flatnonzero(all_ids)[0]]["pose_observed"],
                "total_samples": int(all_ids.sum()), "included_samples": int(ids.sum()),
                **{f"mean_{a}_m_s2": float(mean[k]) for k, a in enumerate("xyz")},
                **{f"std_{a}_m_s2": float(std[k]) for k, a in enumerate("xyz")}})
    csv_file(output / "static-pose-means.csv", summaries)
    angle_intervals = interval_map(root / "data/splits/angles-2026-10-22/manifest.json")
    angles = []
    for acquisition in ("training", "testing"):
        rec = load_csv(angle_dir / f"{acquisition}.csv")
        mask, var, edge, _ = screen(rec, angle_intervals, threshold)
        save_masks(f"angle-{acquisition}-mask", rec, mask, var, edge, masks)
        for seg in np.unique(rec.segment):
            ids = (rec.segment == seg) & mask
            if not ids.any():
                raise ValueError(f"No stable samples in ramp segment {seg}")
            original = rec.rows[np.flatnonzero(ids)[0]]
            raw = rec.xyz[ids].mean(axis=0)
            corr = model.apply(raw)
            target = float(original["angle_deg"])
            row = {"segment_id": int(seg), "acquisition_label": acquisition,
                   "use": "held-out validation (both repeats)", "support": original["support_orientation"],
                   "reference_angle_deg": target, "included_samples": int(ids.sum())}
            for name, val in (("raw", raw), ("corrected", corr)):
                slope = float(slope_degrees(val))
                row[name + "_angle_deg"] = slope
                row[name + "_signed_error_deg"] = slope - target
                row[name + "_absolute_error_deg"] = abs(slope - target)
                row[name + "_magnitude_error_m_s2"] = float(abs(np.linalg.norm(val) - G))
            angles.append(row)
    angles.sort(key=lambda r: r["segment_id"])
    csv_file(output / "angle-validation.csv", angles)
    angle_summary = {name + "_tilt_rmse_deg": float(np.sqrt(np.mean([r[name + "_signed_error_deg"] ** 2 for r in angles])))
                     for name in ("raw", "corrected")}
    angle_summary["aggregation"] = "Eight acquisition means, equal weight; unsigned long-axis slope; no full-vector ramp reference. Two distinct heights only."
    limit = load_csv(angle_dir / "limit.csv")
    magnitude = np.linalg.norm(limit.xyz, axis=1)
    shaking = {"samples": len(limit.t), "max_raw_magnitude_m_s2": float(magnitude.max()),
               "rms_raw_magnitude_deviation_from_g_m_s2": float(np.sqrt(np.mean((magnitude - G) ** 2))),
               "interpretation": "Changing true specific force invalidates gravity-only inclination. No dynamic reference: no affine-error, clipping or failure claim."}
    result = {"static_test": summary, "angle_validation": angle_summary, "shaking": shaking,
              "notebook_all_row_reproduction": baseline_summary,
              "diagnostics": model.diagnostics, "source_sha256": sources,
              "notebook_sha256_unchanged": notebook_hashes,
              "versions": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": matplotlib.__version__},
              "limitations": ["Static tests are within-session repeats, not independent sessions.",
                  "Nominal +/-g references include support alignment error; fit is not intrinsic sensor identification.",
                  "Ruler resolution, contact uncertainty, case and user-selected rate remain unconfirmed.",
                  "Ramps use unsigned long-axis tilt only; signed full reference vectors are not independently established.",
                  "Only two ramp angles; no confirmed affine-model failure; live physical rehearsal pending.",
                  "Low variation is a rest heuristic, not proof of stationarity."]}
    json_file(output / "metrics.json", result)
    make_figures(output, train, train_mask, train_var, train_edge, threshold,
                 test, test_mask, test_var, test_edge, rows, angles, limit)
    markdown_results(output, result, angles, summaries, model)
    if notebook_hashes != {p.name: digest(p) for p in root.glob("*.ipynb")}:
        raise RuntimeError("A teammate notebook changed during analysis")
    print(json.dumps({"static": summary, "angles": angle_summary, "calibration": str(calibration_path)}, indent=2))
    return result


def make_figures(output, train, train_mask, train_var, train_edge, threshold,
                 test, test_mask, test_var, test_edge, metrics, angles, limit):
    fig, axes = plt.subplots(6, 2, figsize=(12, 12), sharey=True)
    for col, (rec, mask, var, edge, title) in enumerate(((train, train_mask, train_var, train_edge, "Training"),
                                                        (test, test_mask, test_var, test_edge, "Testing"))):
        for ax, seg in zip(axes[:, col], np.unique(rec.segment)):
            ids = rec.segment == seg
            t = rec.t[ids] - rec.t[ids][0]
            v = var[ids]
            ax.plot(t, np.minimum(v, threshold * 3), lw=.6, label="local RMS (display capped at 3 x threshold)")
            ax.axhline(threshold, color="coral", ls="--")
            ax.fill_between(t, 0, threshold * 3, where=~mask[ids], color="grey", alpha=.25)
            pose = rec.rows[np.flatnonzero(ids)[0]]["pose_observed"]
            ax.set_title(f"{title} {pose}: {mask[ids].sum()}/{ids.sum()} included", fontsize=9)
            ax.set_ylabel("RMS variation (m/s²)")
            ax.set_ylim(0, threshold * 3)
    axes[-1, 0].set_xlabel("Time within run (s)")
    axes[-1, 1].set_xlabel("Time within run (s)")
    fig.suptitle("Stability masks: grey excluded; policy selected on training only")
    fig.tight_layout()
    fig.savefig(output / "01-rest-masks.png", dpi=140)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    x = np.arange(6)
    for ax, kind, label in zip(axes, ("vector_error_m_s2", "direction_error_deg"), ("Vector error (m/s²)", "Direction error (degrees)")):
        ax.bar(x - .18, [r["raw_" + kind] for r in metrics], .36, label="Raw")
        ax.bar(x + .18, [r["corrected_" + kind] for r in metrics], .36, label="Corrected")
        ax.set_xticks(x, list(POSES))
        ax.set_ylabel(label)
        ax.legend()
    fig.suptitle("Within-session static test: equal-weight pose means / nominal references")
    fig.tight_layout()
    fig.savefig(output / "02-static-validation.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    x = np.arange(len(angles))
    for name, offset in (("raw", -.17), ("corrected", .17)):
        axes[0].bar(x + offset, [r[name + "_absolute_error_deg"] for r in angles], .34, label=name)
        axes[1].scatter([r["reference_angle_deg"] for r in angles], [r[name + "_angle_deg"] for r in angles], label=name)
    axes[0].set_xticks(x, [str(r["segment_id"]) for r in angles])
    axes[0].set_xlabel("Angle acquisition run")
    axes[0].set_ylabel("Absolute tilt error (degrees)")
    axes[1].plot([0, 45], [0, 45], "k--", label="Reference agreement")
    axes[1].set(xlabel="Geometry reference (degrees)", ylabel="Unsigned long-axis tilt (degrees)", xlim=(0, 45), ylim=(0, 45))
    for ax in axes:
        ax.legend()
    fig.suptitle("Held-out angles: both repeats, two heights, screen-up and side support")
    fig.tight_layout()
    fig.savefig(output / "03-angle-validation.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    t = limit.t - limit.t[0]
    # Pixel-bin envelopes retain extremes; no smoothing of scientific values.
    bin_id = np.minimum((t / t[-1] * 1200).astype(int), 1199)
    for axis, label in enumerate("XYZ"):
        lower, upper = [], []
        for k in range(1200):
            values = limit.xyz[bin_id == k, axis]
            lower.append(values.min() if len(values) else np.nan)
            upper.append(values.max() if len(values) else np.nan)
        ax.fill_between(np.linspace(0, t[-1], 1200), lower, upper, alpha=.6, label=label)
    ax.set(xlabel="Time within shaking run (s)", ylabel="Raw acceleration (m/s²)", title="Shaking: real changing input; no independent dynamic reference")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "04-shaking.png", dpi=150)
    plt.close(fig)


def markdown_results(output, result, angles, summaries, model):
    s, a = result["static_test"], result["angle_validation"]
    text = ["# Measured analysis: 23 October 2026", "",
        "Extends the teammate's notebook regression in separate files; notebooks and acquisition datasets are unchanged. Regenerate with `python -m calib.analysis` after editable installation.", "",
        "## Static repeat holdout", "",
        f"Mean vector error: {s['raw_vector_mean_error_m_s2']:.6f} -> {s['corrected_vector_mean_error_m_s2']:.6f} m/s². Vector RMSE: {s['raw_vector_rmse_m_s2']:.6f} -> {s['corrected_vector_rmse_m_s2']:.6f} m/s².", "",
        f"Magnitude RMSE: {s['raw_magnitude_rmse_m_s2']:.6f} -> {s['corrected_magnitude_rmse_m_s2']:.6f} m/s². Direction RMSE: {s['raw_direction_rmse_deg']:.6f} -> {s['corrected_direction_rmse_deg']:.6f} degrees. All metrics average six pose means equally; these are nominal-reference, within-session results.", "",
        "## Angle validation", "",
        f"Unsigned long-axis tilt RMSE: **{a['raw_tilt_rmse_deg']:.6f} -> {a['corrected_tilt_rmse_deg']:.6f} degrees** over eight run means. No full-vector reference is invented from measured signs. Both acquisition-labelled training/testing angle files are validation only.", "",
        "| Run | Support | Reference ° | Raw ° | Corrected ° | Raw absolute error ° | Corrected absolute error ° |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for r in angles:
        text.append(f"| {r['segment_id']} | {r['support']} | {r['reference_angle_deg']:.4f} | {r['raw_angle_deg']:.4f} | {r['corrected_angle_deg']:.4f} | {r['raw_absolute_error_deg']:.4f} | {r['corrected_absolute_error_deg']:.4f} |")
    text += ["", "## Parameters and quality checks", "", "```json", json.dumps(model.to_dict(), indent=2), "```", "",
             "Masks are reproducible, ignored derived artifacts under data/processed/analysis-2026-10-23. The 0.25 s RMS threshold is frozen on static training; fixed 1 s boundary trim and 1 s minimum stable interval apply unchanged to validation. Signal variation does not certify exact alignment or stationarity.", "",
             f"Included static samples: {sum(r['included_samples'] for r in summaries if r['split']=='training')} training and {sum(r['included_samples'] for r in summaries if r['split']=='testing')} testing.", "",
             "## Limits", "", *["- " + s for s in result["limitations"]], "",
             "Shaking is a limit of gravity-only interpretation, not proof of affine sensor failure. Review all four PNGs; positive and negative changes are retained. No thresholds or coefficients were revised after evaluating held-out errors.", ""]
    (output / "README.md").write_text("\n".join(text), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    run(args.root)


if __name__ == "__main__":
    main()
