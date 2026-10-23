"""Evidence for the five sprint questions: linearity, model choice, benefit, limits.

Nothing here is tuned on held-out data. Models are fitted on the static
training pose means only, with the training-frozen stability threshold.
Held-out sets: the static testing repeats (same session) and the twelve ramp
runs recorded on 22 and 23 October (independent sessions). Run with
``python -m calib evidence`` after ``python -m calib analyse``.
"""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .analysis import G, POSES, ROOT, csv_file, digest, interval_map, json_file, pose_means, slope_degrees
from .data import load_csv, read_export, screen
from .model import AffineCalibration

REFERENCES = np.array(list(POSES.values()))
NEW_EXPORT = "data/raw/Acceleration with g 2026-10-23 11-40-57"
COLORS = {"raw": "#9aa5a0", "bias": "#a77f42", "six-position": "#23665e", "full": "#bf7055"}
LABELS = {"raw": "Raw", "bias": "Bias only (3)", "six-position": "Six-position (6)", "full": "Full affine (12)"}


def rms(values):
    return float(np.sqrt(np.mean(np.square(values))))


def direction_deg(values, references):
    values, references = np.atleast_2d(values), np.atleast_2d(references)
    cosine = np.sum(values * references, axis=1) / (np.linalg.norm(values, axis=1) * np.linalg.norm(references, axis=1))
    return np.degrees(np.arccos(np.clip(cosine, -1, 1)))


def nearest_face_deg(values):
    """Angle between the measured vector and the nearest phone axis: 0 at a face, up to 54.7."""
    values = np.atleast_2d(values)
    return np.degrees(np.arccos(np.clip(np.max(np.abs(values), axis=1) / np.linalg.norm(values, axis=1), -1, 1)))


def fit_models(train_means, provenance):
    """Model ladder, all fitted on the same six training pose means."""
    models = {"raw": AffineCalibration(np.eye(3), np.zeros(3), name="Identity / uncalibrated")}
    bias = np.mean(train_means - REFERENCES, axis=0)
    models["bias"] = AffineCalibration(np.eye(3), bias, {**provenance, "method": "Bias only: b = mean(m - a) over six pose means; S = I."},
                                       {"structure": "bias", "parameters": 3}, fitted=True, name="S25 Ultra / bias only")
    models["six-position"] = AffineCalibration.fit(REFERENCES, train_means, {**provenance,
        "reference": "Axial components of the nominal +/-9.81 m/s^2 faces only.",
        "method": "Classical six-position estimator: per-axis least squares m_j = s_j a_j + b_j on the two faces aligned with axis j; off-diagonal S fixed at 0.",
        "selection_note": "Comparison only, added after the full-model held-out results were known. The team keeps the full affine model."},
        structure="diagonal", name="S25 Ultra / six-position diagonal fit")
    models["full"] = AffineCalibration.fit(REFERENCES, train_means, provenance)
    return models


def leave_one_face_out(train_means, structure):
    """Training-only check: fit five faces, predict the sixth (an unseen orientation)."""
    rows = []
    for i, pose in enumerate(POSES):
        keep = np.arange(6) != i
        try:
            if structure == "raw":
                model = AffineCalibration(np.eye(3), np.zeros(3))
            elif structure == "bias":
                model = AffineCalibration(np.eye(3), np.mean(train_means[keep] - REFERENCES[keep], axis=0))
            else:
                model = AffineCalibration.fit(REFERENCES[keep], train_means[keep], {"note": "cross-validation"}, structure=structure)
        except ValueError as error:
            rows.append({"pose": pose, "identifiable": False, "reason": str(error)})
            continue
        value = model.apply(train_means[i])
        rows.append({"pose": pose, "identifiable": True,
                     "vector_error_m_s2": float(np.linalg.norm(value - REFERENCES[i])),
                     "magnitude_error_m_s2": float(np.linalg.norm(value) - G),
                     "direction_error_deg": float(direction_deg(value, REFERENCES[i])[0])})
    usable = [r for r in rows if r["identifiable"]]
    summary = {"identifiable_folds": len(usable)}
    if usable:
        for key in ("vector_error_m_s2", "magnitude_error_m_s2", "direction_error_deg"):
            summary[key.replace("error", "rmse")] = rms([r[key] for r in usable])
    return rows, summary


def angle_runs(root, threshold):
    """Mean vectors of all twelve held-out ramp runs (22 and 23 October)."""
    runs = []
    intervals = interval_map(root / "data/splits/angles-2026-10-22/manifest.json")
    for acquisition in ("training", "testing"):
        rec = load_csv(root / f"data/processed/angles-2026-10-22/{acquisition}.csv")
        mask, *_ = screen(rec, intervals, threshold)
        for seg in np.unique(rec.segment):
            ids = (rec.segment == seg) & mask
            first = rec.rows[np.flatnonzero(rec.segment == seg)[0]]
            runs.append({"session": "2026-10-22", "run": int(seg), "support": first["support_orientation"],
                         "pair": int(first["pair_id"]), "height_m": float(first["height_m"]),
                         "reference_deg": float(first["angle_deg"]), "samples": int(ids.sum()),
                         "mean": rec.xyz[ids].mean(axis=0), "std": rec.xyz[ids].std(axis=0)})
    protocol = json.loads((root / "data/splits/angles-2026-10-23/protocol.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "data/splits/angles-2026-10-23/manifest.json").read_text(encoding="utf-8"))
    rec, new_intervals = read_export(root / NEW_EXPORT)
    mask, *_ = screen(rec, new_intervals, threshold)
    length = protocol["contact_spacing_m"]
    for seg, h, audit in zip(sorted(new_intervals), protocol["height_order_m"], manifest["segments"]):
        ids = (rec.segment == seg) & mask
        mean = rec.xyz[ids].mean(axis=0)
        # Independent re-reading must reproduce the frozen four-height audit exactly.
        if int(ids.sum()) != audit["included_samples"] or not np.allclose(mean, audit["mean_xyz_m_s2"], rtol=0, atol=1e-9):
            raise ValueError(f"Four-height run {seg} does not reproduce its frozen audit")
        runs.append({"session": "2026-10-23", "run": int(seg), "support": protocol["support_orientation"], "pair": None,
                     "height_m": float(h), "reference_deg": float(np.degrees(np.arcsin(h / length))), "samples": int(ids.sum()),
                     "mean": mean, "std": rec.xyz[ids].std(axis=0)})
    return runs


def quantization(root, folders):
    """Every exported sample sits on a fixed lattice: the smallest output step."""
    device = {}
    with (root / folders[0] / "meta/device.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["property"].startswith("accelerometer "):
                device[row["property"].removeprefix("accelerometer ")] = row["value"]
    resolution = float(device["Resolution"])
    rows = []
    for folder in folders:
        rec, intervals = read_export(root / folder)
        quiet = rec.segment == min(intervals)
        for axis, name in enumerate("xyz"):
            levels = np.unique(rec.xyz[quiet, axis])
            # Values are float32 multiples of the reported resolution: near 9.8 m/s^2 the
            # float32 spacing (~1e-6) is 2e-4 of a step, so allow 1e-3 of a step.
            offset = rec.xyz[:, axis] / resolution
            rows.append({"export": folder.split("/")[-1], "axis": name,
                         "median_level_spacing_in_steps": float(np.median(np.diff(levels)) / resolution),
                         "fraction_on_lattice": float(np.mean(np.abs(offset - np.round(offset)) < 1e-3)),
                         "distinct_levels_first_run": int(len(levels)), "first_run_samples": int(quiet.sum())})
    return device, rows


def shaking_limits(root, device):
    limit = load_csv(root / "data/processed/angles-2026-10-22/limit.csv")
    t, xyz = limit.t - limit.t[0], limit.xyz
    magnitude = np.linalg.norm(xyz, axis=1)
    full_scale = float(device["Range"])
    windows = []
    for start in np.arange(0, t[-1] - 1, 1.0):
        ids = (t >= start) & (t < start + 1)
        mean = xyz[ids].mean(axis=0)
        windows.append({"start_s": float(start), "mean_magnitude_m_s2": float(np.linalg.norm(mean)),
                        "long_axis_tilt_deg": float(slope_degrees(mean))})
    peaks = {a: float(np.max(np.abs(xyz[:, k]))) for k, a in enumerate("xyz")}
    return {"samples": int(len(t)), "duration_s": float(t[-1]),
            "reported_full_scale_m_s2": full_scale, "peak_abs_axis_m_s2": peaks,
            "peak_fraction_of_full_scale": max(peaks.values()) / full_scale,
            "samples_at_or_beyond_full_scale": int(np.sum(np.abs(xyz) >= full_scale)),
            "max_vector_magnitude_m_s2": float(magnitude.max()),
            "rms_magnitude_deviation_from_g_m_s2": rms(magnitude - G),
            "fraction_within_still_flag_0_35": float(np.mean(np.abs(magnitude - G) <= .35)),
            "fraction_above_2g": float(np.mean(magnitude > 2 * G)),
            "one_second_mean_magnitude_range_m_s2": [min(w["mean_magnitude_m_s2"] for w in windows), max(w["mean_magnitude_m_s2"] for w in windows)],
            "one_second_mean_tilt_range_deg": [min(w["long_axis_tilt_deg"] for w in windows), max(w["long_axis_tilt_deg"] for w in windows)],
            "windows": windows,
            "interpretation": "The input is no longer gravity alone, so the gravity-only calibration model a = g fails. "
                              "No independent dynamic reference exists: this does not show that the sensor's m = S a + b response fails."}, limit


def run(root=ROOT):
    root = Path(root)
    output = root / "results/evidence-2026-10-23"
    output.mkdir(parents=True, exist_ok=True)
    policy = json.loads((root / "results/analysis-2026-10-23/frozen-policy.json").read_text(encoding="utf-8"))
    threshold = float(policy["stability_threshold_m_s2"])
    intervals = interval_map(root / "data/splits/static-2026-10-21/manifest.json")
    means = {}
    for split in ("training", "testing"):
        rec = load_csv(root / f"data/processed/static-2026-10-21/{split}.csv")
        mask, *_ = screen(rec, intervals, threshold)
        means[split] = pose_means(rec, mask)
        if split == "training":
            noise = {a: float(np.median([rec.xyz[mask & (rec.segment == s), k].std() for s in np.unique(rec.segment)]))
                     for k, a in enumerate("xyz")}
    train, test = means["training"], means["testing"]
    provenance = {key: policy[key] for key in ("training_session", "files", "training_sha256", "gravity_m_s2",
                                               "stability_threshold_m_s2", "stability_policy")}
    models = fit_models(train, {**provenance, "reference": policy["reference"], "method": policy["method"]})
    archived = AffineCalibration.load(root / "calibration/fit-static-2026-10-21.json")
    if not (np.allclose(archived.S, models["full"].S, rtol=0, atol=1e-12) and np.allclose(archived.b, models["full"].b, rtol=0, atol=1e-12)):
        raise ValueError("Full refit differs from the archived frozen calibration")
    models["full"] = archived
    runs = angle_runs(root, threshold)
    ramp_means = np.array([r["mean"] for r in runs])
    references = np.array([r["reference_deg"] for r in runs])
    new = np.array([r["session"] == "2026-10-23" for r in runs])
    raised = new & (references > 0)

    comparison, ramp_rows = [], [{"session": r["session"], "run": r["run"], "support": r["support"], "height_m": r["height_m"],
                                  "reference_deg": r["reference_deg"], "included_samples": r["samples"]} for r in runs]
    corrected_ramps = {}
    for name, model in models.items():
        static = model.apply(test)
        trained = model.apply(train)
        ramps = model.apply(ramp_means)
        corrected_ramps[name] = ramps
        tilt = slope_degrees(ramps)
        _, loo = leave_one_face_out(train, {"six-position": "diagonal"}.get(name, name))
        comparison.append({
            "model": name, "parameters": {"raw": 0, "bias": 3, "six-position": 6, "full": 12}[name],
            "train_fit_vector_rmse_m_s2": rms(np.linalg.norm(trained - REFERENCES, axis=1)),
            "train_magnitude_rmse_m_s2": rms(np.linalg.norm(trained, axis=1) - G),
            "loo_folds_identifiable": loo["identifiable_folds"],
            "loo_vector_rmse_m_s2": loo.get("vector_rmse_m_s2"), "loo_direction_rmse_deg": loo.get("direction_rmse_deg"),
            "static_test_vector_rmse_m_s2": rms(np.linalg.norm(static - REFERENCES, axis=1)),
            "static_test_magnitude_rmse_m_s2": rms(np.linalg.norm(static, axis=1) - G),
            "static_test_tilt_rmse_deg": rms(direction_deg(static, REFERENCES)),
            "ramp_magnitude_rmse_m_s2": rms(np.linalg.norm(ramps, axis=1) - G),
            "ramp_magnitude_max_abs_m_s2": float(np.max(np.abs(np.linalg.norm(ramps, axis=1) - G))),
            "ramp_tilt_rmse_2026_10_22_deg": rms(tilt[~new] - references[~new]),
            "ramp_tilt_rmse_2026_10_23_deg": rms(tilt[new] - references[new]),
            "ramp_tilt_rmse_2026_10_23_raised_deg": rms(tilt[raised] - references[raised]),
            "max_tilt_change_vs_raw_deg": float(np.max(np.abs(tilt - slope_degrees(ramp_means))))})
        for row, value, angle in zip(ramp_rows, ramps, tilt):
            row[f"{name}_tilt_deg"] = float(angle)
            row[f"{name}_magnitude_error_m_s2"] = float(np.linalg.norm(value) - G)
    csv_file(output / "model-comparison.csv", comparison)
    csv_file(output / "ramp-tilt.csv", ramp_rows)

    # Q2: reference-free homogeneity test. At rest |a| = g exactly, whatever the angle.
    six = models["six-position"]
    still = np.vstack([test, ramp_means])
    labels = [f"static test {p}" for p in POSES] + [f"{r['session']} run {r['run']} ({r['support']}, {r['height_m']*100:.0f} cm)" for r in runs]
    corrected = six.apply(still)
    linearity = []
    for label, raw, value in zip(labels, still, corrected):
        fractions = np.abs(value) / np.linalg.norm(value)
        linearity.append({"orientation": label, "angle_from_nearest_face_deg": float(nearest_face_deg(value)[0]),
                          **{f"input_fraction_{a}": float(f) for a, f in zip("xyz", fractions)},
                          "raw_magnitude_error_m_s2": float(np.linalg.norm(raw) - G),
                          "six_position_magnitude_error_m_s2": float(np.linalg.norm(value) - G),
                          "full_magnitude_error_m_s2": float(np.linalg.norm(models["full"].apply(raw)) - G)})
    csv_file(output / "linearity.csv", linearity)
    intermediate = np.array([r["angle_from_nearest_face_deg"] > 5 for r in linearity])
    six_err = np.array([r["six_position_magnitude_error_m_s2"] for r in linearity])
    fractions = np.array([[r[f"input_fraction_{a}"] for a in "xyz"] for r in linearity])
    homogeneity = {
        "test": "Six-position model pinned only at a_j = +/-g on each axis; it predicts every intermediate input k*g by proportional scaling. Check |a_hat| = g at held-out still orientations (no angle reference needed).",
        "orientations": len(linearity), "intermediate_orientations": int(intermediate.sum()),
        "intermediate_input_fraction_range": [float(fractions[intermediate][fractions[intermediate] > .1].min()), float(fractions[intermediate].max())],
        "angle_from_nearest_face_range_deg": [float(min(r["angle_from_nearest_face_deg"] for r in linearity)), float(max(r["angle_from_nearest_face_deg"] for r in linearity))],
        "faces_rmse_m_s2": rms(six_err[~intermediate]), "intermediate_rmse_m_s2": rms(six_err[intermediate]),
        "max_abs_m_s2": float(np.max(np.abs(six_err))), "max_abs_fraction_of_g": float(np.max(np.abs(six_err)) / G),
        "raw_intermediate_rmse_m_s2": rms([r["raw_magnitude_error_m_s2"] for r, k in zip(linearity, intermediate) if k]),
        "full_intermediate_rmse_m_s2": rms([r["full_magnitude_error_m_s2"] for r, k in zip(linearity, intermediate) if k]),
        "full_intermediate_mean_m_s2": float(np.mean([r["full_magnitude_error_m_s2"] for r, k in zip(linearity, intermediate) if k])),
        "caveat": "Bounds any departure from proportional scaling (and unmodelled cross-axis coupling) within |a_j| <= g on the gravity sphere; inputs above 1 g are untested."}

    pair_tilt = {}
    for r, angle in zip(runs, slope_degrees(ramp_means)):
        if r["pair"] is not None:
            pair_tilt.setdefault(r["pair"], []).append(float(angle))
    flat = {"2026-10-21 static +Z training": float(np.linalg.norm(train[list(POSES).index("+Z")])),
            "2026-10-23 0 cm run": float(np.linalg.norm(ramp_means[new][0]))}
    raw_gap = (slope_degrees(ramp_means) - references)[references > 0]
    repeatability = {
        "static_repeat_difference_m_s2": {p: float(np.linalg.norm(a - b)) for p, a, b in zip(POSES, train, test)},
        "static_repeat_difference_rms_m_s2": rms(np.linalg.norm(train - test, axis=1)),
        "ramp_repeat_tilt_difference_deg": {str(k): abs(v[0] - v[1]) for k, v in pair_tilt.items()},
        "screen_up_raw_magnitude_across_days_m_s2": flat,
        "per_sample_noise_std_m_s2": noise,
        "raised_ramp_raw_gap_to_contact_line_deg": [float(raw_gap.min()), float(raw_gap.max())],
        "geometry_sensitivity_deg_per_mm": {"height": float(np.degrees(1e-3 / (0.16 * np.cos(np.radians(references[raised].max()))))),
                                            "length_at_largest_angle": float(np.degrees(np.tan(np.radians(references.max())) * 1e-3 / 0.16))}}
    device, lattice = quantization(root, ["data/raw/Acceleration with g 2026-10-21 17-43-29",
                                          "data/raw/Acceleration with g 2026-10-22 10-55-51", NEW_EXPORT])
    shaking, limit = shaking_limits(root, device)
    step = float(device["Resolution"])
    limits = {"device": {k: device[k] for k in ("Name", "Vendor", "Range", "Resolution")},
              "quantization": {"rows": lattice, "minimum_fraction_on_lattice": min(r["fraction_on_lattice"] for r in lattice),
                               "step_m_s2": step, "step_as_tilt_deg": float(np.degrees(step / G)),
                               "averaging_note": "Noise (about 1.7 steps rms) dithers the staircase, so means of many samples stay linear."},
              "shaking": {k: v for k, v in shaking.items() if k != "windows"}}
    diagnostics = {"full": models["full"].diagnostics, "six-position": models["six-position"].diagnostics,
                   "rank_examples": rank_examples()}
    loo_tables = {name: leave_one_face_out(train, {"six-position": "diagonal"}.get(name, name))[0] for name in models}
    result = {"schema_version": 1, "frozen_threshold_m_s2": threshold, 
              "models": {name: {"S": m.S.tolist(), "b": m.b.tolist()} for name, m in models.items()},
              "comparison": comparison, "leave_one_face_out": loo_tables, "homogeneity": homogeneity,
              "repeatability": repeatability, "limits": limits, "diagnostics": diagnostics,
              "input_sha256": {p: digest(root / p) for p in ("calibration/fit-static-2026-10-21.json", "results/analysis-2026-10-23/frozen-policy.json",
                                                            "data/processed/static-2026-10-21/training.csv", "data/processed/static-2026-10-21/testing.csv",
                                                            "data/processed/angles-2026-10-22/training.csv", "data/processed/angles-2026-10-22/testing.csv",
                                                            "data/processed/angles-2026-10-22/limit.csv", NEW_EXPORT + "/Raw Data.csv")}}
    json_file(output / "metrics.json", result)
    figures(output, linearity, comparison, runs, corrected_ramps, ramp_means, root, shaking, limit, device)
    write_readme(output, result)
    print(json.dumps({"comparison": comparison, "homogeneity": homogeneity}, indent=2))
    return result


def rank_examples():
    """Q3: which pose sets identify S and b?"""
    faces = dict(zip(POSES, REFERENCES))
    sets = {"all six faces": list(POSES), "four faces +X,+Y,+Z,-X": ["+X", "+Y", "+Z", "-X"],
            "planar +/-X, +/-Y": ["+X", "-X", "+Y", "-Y"], "three faces +X,+Y,+Z": ["+X", "+Y", "+Z"],
            "one pose repeated": ["+Z", "+Z", "+Z"]}
    return {name: int(np.linalg.matrix_rank(np.column_stack([[faces[p] for p in poses], np.ones(len(poses))]))) for name, poses in sets.items()}


def style(ax):
    ax.grid(axis="y", color="#e1e6e1", linewidth=.6)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#aebcb1")
    ax.tick_params(labelsize=8, length=2, color="#aebcb1")


def save(fig, path):
    fig.savefig(path, dpi=220, facecolor="#fffefa")
    plt.close(fig)


def figures(output, linearity, comparison, runs, corrected_ramps, ramp_means, root, shaking, limit, device):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})
    # 1. Linearity: magnitude must stay g at every still orientation.
    fig, ax = plt.subplots(figsize=(6.4, 2.35))
    angle = [r["angle_from_nearest_face_deg"] for r in linearity]
    for key, name, marker in (("raw", "raw", "o"), ("full", "full", "s"), ("six_position", "six-position", "D")):
        ax.scatter(angle, [r[f"{key}_magnitude_error_m_s2"] for r in linearity], s=22, marker=marker,
                   color=COLORS[name], label=LABELS[name], zorder=3, edgecolor="white", linewidth=.4)
    ax.axhline(0, color="#233431", lw=.8)
    ax.axhspan(-.04, .04, color=COLORS["six-position"], alpha=.07, zorder=0, lw=0)
    ax.axvspan(-1, 5, color="#eef4ef", zorder=0)
    ax.text(2, -.137, "near a face (< 5°)", ha="center", va="bottom", fontsize=6.5, color="#66736e")
    ax.text(26, -.137, "held-out ramp runs, 22 and 23 October", ha="center", va="bottom", fontsize=6.5, color="#66736e")
    ax.text(40.6, .041, "±0.04 m/s² = ±0.4 % of g", ha="right", va="bottom", fontsize=6.5, color=COLORS["six-position"])
    ax.set(xlim=(-1, 41), ylim=(-.14, .12), xlabel="Angle of gravity from the nearest phone axis (°)", ylabel="|â| − g  (m/s²)")
    ax.legend(frameon=False, fontsize=7, ncol=3, loc="lower center", bbox_to_anchor=(.5, 1), borderaxespad=.2)
    style(ax)
    fig.tight_layout(pad=.4)
    save(fig, output / "fig1-linearity.png")
    # 2. Held-out benefit by model.
    order = ["raw", "bias", "six-position", "full"]
    rows = {r["model"]: r for r in comparison}
    panels = (("static_test_vector_rmse_m_s2", "Static repeats:\nvector RMSE (m/s²)"),
              ("static_test_tilt_rmse_deg", "Static repeats:\ntilt RMSE (°)"),
              ("ramp_magnitude_rmse_m_s2", "12 runs, later days:\n|â| − g RMSE (m/s²)"))
    fig, axes = plt.subplots(1, 3, figsize=(6.4, 2.05))
    for ax, (key, title) in zip(axes, panels):
        values = [rows[m][key] for m in order]
        ax.bar(range(4), values, .68, color=[COLORS[m] for m in order])
        for x, v in enumerate(values):
            ax.text(x, v, f"{v:.3f}" if v < 1 else f"{v:.2f}", ha="center", va="bottom", fontsize=6.5)
        ax.set_title(title, fontsize=7.5, color="#233431")
        ax.set_xticks(range(4), ["Raw", "Bias", "Six-\nposition", "Full"], fontsize=7)
        ax.set_ylim(0, max(values) * 1.22)
        style(ax)
    fig.tight_layout(pad=.4, w_pad=1.2)
    save(fig, output / "fig2-benefit.png")
    # 3. Ramp tilt: calibration shifts are small next to the contact-line gap.
    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    refs = np.array([r["reference_deg"] for r in runs])
    ax.plot([0, 46], [0, 46], color="#233431", lw=.8, ls="--")
    ax.text(31, 33.5, "tilt = asin(h/L)", rotation=38, fontsize=6.5, color="#233431")
    for name, marker, offset in (("raw", "o", -.5), ("six-position", "D", 0), ("full", "s", .5)):
        ax.scatter(refs + offset, slope_degrees(corrected_ramps[name]), s=16, marker=marker, color=COLORS[name],
                   label=LABELS[name], zorder=3, edgecolor="white", linewidth=.3)
    shift = max(r["max_tilt_change_vs_raw_deg"] for r in comparison if r["model"] != "raw")
    gap = -(slope_degrees(ramp_means) - refs)[refs > 0]
    ax.text(45, 1, f"Calibration moves tilt ≤ {shift:.1f}°.\nRaised runs read {gap.min():.1f}–{gap.max():.1f}°\nbelow the contact line,\nrepeatable to 0.003°.",
            ha="right", va="bottom", fontsize=6.3, color="#233431")
    ax.set(xlim=(-2, 46), ylim=(-2, 46), xlabel="Contact-line angle asin(h/L) (°)", ylabel="Measured long-axis tilt (°)")
    ax.legend(frameon=False, fontsize=6.5, loc="upper left")
    style(ax)
    fig.tight_layout(pad=.4)
    save(fig, output / "fig3-ramp-tilt.png")
    # 4. Limits: quantization staircase and shaking beyond the gravity assumption.
    fig, (left, right) = plt.subplots(1, 2, figsize=(6.4, 2.2), gridspec_kw={"width_ratios": [1, 1.6]})
    rec, intervals = read_export(root / "data/raw/Acceleration with g 2026-10-21 17-43-29")
    quiet = rec.segment == min(intervals)
    values, counts = np.unique(rec.xyz[quiet, 0], return_counts=True)
    step = float(device["Resolution"])
    left.bar(values * 1000, counts, width=step * 1000 * .35, color=COLORS["six-position"])
    left.set(xlabel="x output, still pose (mm/s²)", ylabel="Samples")
    left.set_title(f"Only {len(values)} distinct levels, {step*1000:.2f} mm/s² apart", fontsize=7.5)
    style(left)
    t = limit.t - limit.t[0]
    magnitude = np.linalg.norm(limit.xyz, axis=1)
    bins = np.minimum((t / t[-1] * 600).astype(int), 599)
    lo = [magnitude[bins == k].min() for k in range(600)]
    hi = [magnitude[bins == k].max() for k in range(600)]
    centers = np.linspace(0, t[-1], 600)
    right.fill_between(centers, lo, hi, color=COLORS["full"], alpha=.55, lw=0, label="|m| (envelope)")
    right.plot([w["start_s"] + .5 for w in shaking["windows"]], [w["mean_magnitude_m_s2"] for w in shaking["windows"]],
               color="#233431", lw=1, label="1 s mean |m|")
    right.axhline(G, color=COLORS["six-position"], lw=.9, ls="--", label="g")
    right.axhline(float(device["Range"]), color="#a77f42", lw=.9, ls=":", label="±16 g full scale (one axis)")
    right.set(xlabel="Time in shaking run (s)", ylabel="m/s²", ylim=(0, 205))
    right.legend(frameon=False, fontsize=6.3, loc="upper right", ncol=2)
    style(right)
    fig.tight_layout(pad=.4, w_pad=1.4)
    save(fig, output / "fig4-limits.png")


def write_readme(output, result):
    c = {r["model"]: r for r in result["comparison"]}
    h, rep, lim = result["homogeneity"], result["repeatability"], result["limits"]
    lines = ["# Evidence for the five questions: 23 October 2026", "",
             "Generated by `python -m calib evidence`. Every model is fitted on the six static **training** pose means with the training-frozen stability threshold; nothing is tuned on held-out data. "
             "The delivered calibration is the full model (`calibration/fit-static-2026-10-21.json`). The other rows are comparisons, added after the full model's held-out results were known, so they are not blind tests.", "",
             "## Model comparison", "",
             "| Model | Params | Train LOO tilt (°) | Static test vector (m/s²) | Static test tilt (°) | Static test \\|â\\|−g (m/s²) | 12 later runs \\|â\\|−g (m/s²) | Ramp tilt 22 Oct / 23 Oct (°) |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name in ("raw", "bias", "six-position", "full"):
        r = c[name]
        loo = "not identifiable" if r["loo_direction_rmse_deg"] is None else f"{r['loo_direction_rmse_deg']:.3f}"
        lines.append(f"| {LABELS[name]} | {r['parameters']} | {loo} | {r['static_test_vector_rmse_m_s2']:.4f} | {r['static_test_tilt_rmse_deg']:.3f} | "
                     f"{r['static_test_magnitude_rmse_m_s2']:.4f} | {r['ramp_magnitude_rmse_m_s2']:.4f} | {r['ramp_tilt_rmse_2026_10_22_deg']:.3f} / {r['ramp_tilt_rmse_2026_10_23_deg']:.3f} |")
    lines += ["", "LOO: leave one training face out, fit the other five, predict the unseen face (training data only). The six-position model needs both faces of every axis, so it has no five-face fit.", "",
              "## Linearity (homogeneity) test", "",
              f"{h['test']} Across {h['intermediate_orientations']} intermediate orientations (input fractions {h['intermediate_input_fraction_range'][0]:.2f}–{h['intermediate_input_fraction_range'][1]:.2f} of g per axis), "
              f"RMSE {h['intermediate_rmse_m_s2']:.4f} m/s², maximum |error| {h['max_abs_m_s2']:.4f} m/s² ({100*h['max_abs_fraction_of_g']:.2f} % of g). Raw: {h['raw_intermediate_rmse_m_s2']:.4f}; full affine: {h['full_intermediate_rmse_m_s2']:.4f} (mean {h['full_intermediate_mean_m_s2']:+.4f}). {h['caveat']}", "",
              "## Repeatability", "",
              f"Static repeat-to-repeat difference RMS {rep['static_repeat_difference_rms_m_s2']:.4f} m/s² (per pose: " + ", ".join(f"{p} {v:.4f}" for p, v in rep["static_repeat_difference_m_s2"].items()) + "). "
              f"Ramp repeats agree within {max(rep['ramp_repeat_tilt_difference_deg'].values()):.4f}°. On the eleven raised runs, raw tilt sits {abs(rep['raised_ramp_raw_gap_to_contact_line_deg'][1]):.2f}–{abs(rep['raised_ramp_raw_gap_to_contact_line_deg'][0]):.2f}° below asin(h/L). "
              "Per-sample noise std: " + ", ".join(f"{a} {v:.4f}" for a, v in rep["per_sample_noise_std_m_s2"].items()) + " m/s².", "",
              "## Limits", "",
              f"Quantization: on every axis of all three exports, at least {100*lim['quantization']['minimum_fraction_on_lattice']:.2f} % of samples are integer multiples of the reported resolution {lim['quantization']['step_m_s2']:.7f} m/s² (= {lim['quantization']['step_as_tilt_deg']:.3f}° of tilt), within float32 storage precision. "
              f"Shaking peak per axis {max(lim['shaking']['peak_abs_axis_m_s2'].values()):.1f} m/s² = {100*lim['shaking']['peak_fraction_of_full_scale']:.0f} % of the reported ±{float(lim['device']['Range']):.1f} m/s² range; "
              f"{lim['shaking']['samples_at_or_beyond_full_scale']} samples at full scale. Only {100*lim['shaking']['fraction_within_still_flag_0_35']:.1f} % of shaking samples are within 0.35 m/s² of g. {lim['shaking']['interpretation']}", "",
              "Files: `metrics.json`, `model-comparison.csv`, `linearity.csv`, `ramp-tilt.csv`, four report figures.", ""]
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    run(args.root)


if __name__ == "__main__":
    main()
