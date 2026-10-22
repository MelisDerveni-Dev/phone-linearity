"""Audit/split the nine-run angle export without fitting or altering raw data.

Uses original acquisition events and explicit geometry from a protocol JSON.
All rows survive in split CSVs; a separate inclusion flag trims one second at
each quiet run boundary. This timing guard is not a scientific rest detector.
Only the standard library is required.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics

from split_static_recording import (
    HEADERS, ROOT, display_path, partition, read_intervals, read_samples, sha256,
)

EXTRA = ["source_row", "segment_id", "pair_id", "split", "kind", "support_orientation", "height_m",
         "contact_spacing_m", "angle_deg", "include", "exclusion_reason"]


def angle_degrees(height, length):
    if not all(math.isfinite(v) for v in (height, length)) or not 0 <= height <= length or length <= 0:
        raise ValueError("Require finite 0 <= height <= contact spacing and positive spacing")
    return math.degrees(math.asin(height / length))


def boundary_mask(times, start, end, trim):
    if not math.isfinite(trim) or trim < 0 or end - start <= 2 * trim:
        raise ValueError("Trim must be nonnegative and leave a nonempty interval")
    return [start + trim <= t < end - trim for t in times]


def preprocess(source, protocol_path, output, audit):
    source, protocol_path, output, audit = [Path(p).resolve() for p in (source, protocol_path, output, audit)]
    for dest in (output, audit):
        if dest == source or dest.is_relative_to(source) or dest.is_relative_to(ROOT / "data/raw"):
            raise ValueError("Outputs must stay outside raw data")
    if output == audit or output.is_relative_to(audit) or audit.is_relative_to(output):
        raise ValueError("Output and audit directories must be separate")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    raw = source / "Raw Data.csv"
    events = source / "meta/time.csv"
    paths = [raw, events, source / "meta/device.csv", protocol_path]
    hashes = {display_path(p): sha256(p) for p in paths}
    intervals = read_intervals(events)
    rows, samples = read_samples(raw)
    groups = partition(samples, intervals)
    runs = protocol["runs"]
    if len(runs) != len(groups) or len(runs) != 9:
        raise ValueError("This protocol requires eight quiet runs and a ninth shaking run")
    for i, run in enumerate(runs):
        expected = "limit" if i == 8 else ("training" if i % 2 == 0 else "testing")
        if run["split"] != expected or run["kind"] != ("shaking" if i == 8 else "ramp"):
            raise ValueError("Expected four consecutive training/testing pairs then shaking")
        if i < 8 and run["pair_id"] != i // 2 + 1:
            raise ValueError("Invalid pair assignment")
    for i in range(0, 8, 2):
        if runs[i].get("height_m") != runs[i + 1].get("height_m"):
            raise ValueError("Pair members must have the same specified height")
        if runs[i].get("support_orientation") != runs[i + 1].get("support_orientation"):
            raise ValueError("Pair members must have the same support orientation")
    spacing = protocol.get("contact_spacing_m")
    trim = protocol["boundary_trim_s"]
    if trim != 1.0:
        raise ValueError("This reviewed protocol uses exactly a one-second boundary trim")
    records = []
    segments = []
    for run, interval, indices in zip(runs, intervals, groups):
        height = run.get("height_m")
        angle = None if height is None or spacing is None else angle_degrees(height, spacing)
        quiet = run["kind"] == "ramp"
        mask = boundary_mask([samples[i][0] for i in indices], interval["start_s"], interval["end_s"], trim) if quiet else [True] * len(indices)
        selected = [i for i, keep in zip(indices, mask) if keep]
        if not selected:
            raise ValueError("No samples remain inside a quiet run")
        segment = {**interval, **run, "angle_deg": angle, "samples": len(indices),
                   "included_samples": len(selected), "first_source_row": indices[0] + 1,
                   "last_source_row": indices[-1] + 1,
                   "mean_xyz_m_s2": [statistics.mean(samples[i][a] for i in selected) for a in (1, 2, 3)],
                   "std_xyz_m_s2": [statistics.pstdev(samples[i][a] for i in selected) for a in (1, 2, 3)],
                   "min_xyz_m_s2": [min(samples[i][a] for i in indices) for a in (1, 2, 3)],
                   "max_xyz_m_s2": [max(samples[i][a] for i in indices) for a in (1, 2, 3)],
                   "max_vector_magnitude_m_s2": max(math.hypot(*samples[i][1:4]) for i in indices)}
        segments.append(segment)
        for i, keep in zip(indices, mask):
            records.append((run["split"], rows[i] + [i + 1, interval["segment_id"], run["pair_id"],
                run["split"], run["kind"], run.get("support_orientation", ""), height if height is not None else "",
                spacing if spacing is not None and quiet else "", angle if angle is not None else "",
                int(keep), "" if keep else "acquisition_boundary_1s"]))
    # All protocol/data validation precedes output creation.
    output.mkdir(parents=True, exist_ok=True)
    audit.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for split in ("training", "testing", "limit"):
        path = output / f"{split}.csv"
        selected = [row for name, row in records if name == split]
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(HEADERS + EXTRA)
            writer.writerows(selected)
        outputs[split] = {"path": display_path(path), "sha256": sha256(path),
                          "samples": len(selected), "included_samples": sum(int(r[-2]) for r in selected)}
    fields = ["segment_id", "pair_id", "kind", "split", "support_orientation", "height_m", "angle_deg", "start_s", "end_s",
              "duration_s", "samples", "included_samples", "first_source_row", "last_source_row"]
    with (audit / "segments.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(segments)
    report = {"schema_version": 1, "source_sha256": hashes, "samples": len(rows),
              "outputs": outputs, "segments": segments, "protocol": protocol,
              "boundary_convention": "Original START/PAUSE [start,end), no guessed 30-second cuts.",
              "preprocessing": "All original strings/rows retained. Quiet-run include=1 only in [start+1s,end-1s). Shaking entirely retained. No smoothing/resampling/outlier removal or data-dependent selection.",
              "geometry_status": "user-supplied contact geometry; dimensional uncertainty unspecified" if spacing is not None else "pending contact spacing confirmation; angle columns blank",
              "limitations": ["Training/testing are acquisition labels; ramps remain separate from six-face calibration fitting.",
                              "Pairs come from one session; independent repositioning not confirmed.",
                              "Timing trim is not rest detection; inspect the audit plot and per-run variability.",
                              "Screen-up versus side support is user-confirmed; exact signed reference vectors and ruler/contact uncertainty remain unspecified.",
                              "Shaking changes true input and invalidates gravity-only tilt interpretation; it does not establish affine accelerometer failure.",
                              "No fitting, corrected errors, improvement or clipping conclusion."]}
    if any(sha256(p) != hashes[display_path(p)] for p in paths):
        raise ValueError("Source changed while processing; rerun")
    (audit / "manifest.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_plot(audit / "trace-review.svg", samples, groups, segments, trim)
    lines = ["# Angle and shaking acquisition: 22 October 2026", "",
             "All original rows are retained in versioned, reproducible split CSVs. Use `include=1` for the timing-trimmed quiet-run summaries; no automated rest detector is claimed.", "",
             "| Run | Pair | Support | Split | Seconds | All / included samples | Height (m) | Angle (degrees) |",
             "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |"]
    for s in segments:
        lines.append(f"| {s['segment_id']} | {s['pair_id']} | {s.get('support_orientation', '')} | {s['split']} | {s['duration_s']:.3f} | {s['samples']} / {s['included_samples']} | {s.get('height_m')} | {s['angle_deg']} |")
    lines += ["", "Angles use asin(height / contact spacing), relative to horizontal, only when both geometry fields are supplied. User-confirmed contact spacing is 16 cm along the phone (the hypotenuse), with 10 cm height for runs 1–4 and 5 cm for runs 5–8. Thus angles are 38.6822 and 18.2100 degrees. Runs 1–2 and 5–6 are screen-up; runs 3–4 and 7–8 are on the side, screen perpendicular to the table. The shaking run has no reference angle. Unknown heights/spacing stay blank in CSVs. Do not infer independent geometry from sensor readings.", "",
              "See `manifest.json` for hashes, exact times, per-run statistics and limitations; `trace-review.svg` shows all runs, with excluded boundary regions shaded. Each quiet panel uses the same axis scale; shaking uses its own labelled scale to retain extremes. Pixel-column min/max envelopes preserve spikes.", "",
              *report["limitations"], ""]
    (audit / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def write_plot(path, samples, groups, segments, trim):
    """Standalone SVG, per-pixel extrema rather than decimation/averaging."""
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1550" viewBox="0 0 1080 1550">',
             '<rect width="1080" height="1550" fill="white"/>',
             '<g font-family="sans-serif" font-size="13">',
             '<text x="25" y="23">Original acceleration: X teal, Y coral, Z blue; grey = excluded boundary (not rest detection)</text>']
    for k, (indices, s) in enumerate(zip(groups, segments)):
        top, left, width, height = 58 + k * 165, 65, 970, 112
        bound = 12 if k < 8 else max(12, math.ceil(max(abs(samples[i][a]) for i in indices for a in (1, 2, 3)) / 10) * 10)
        duration = s["duration_s"]
        parts.append(f'<text x="25" y="{top-9}">Run {k+1} / {s["split"]}: {duration:.2f} s; scale ±{bound} m/s²</text>')
        parts.append(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" fill="#fafafa" stroke="#888"/>')
        if k < 8:
            edge = width * trim / duration
            for x in (left, left + width - edge):
                parts.append(f'<rect x="{x:.2f}" y="{top}" width="{edge:.2f}" height="{height}" fill="#ddd"/>')
        parts.append(f'<path d="M {left} {top+height/2} h {width}" stroke="#bbb"/>')
        for axis, color in ((1, "#087f80"), (2, "#d44e39"), (3, "#345cba")):
            bins = {}
            for i in indices:
                col = min(width - 1, int((samples[i][0] - s["start_s"]) / duration * width))
                value = samples[i][axis]
                lo, hi = bins.get(col, (value, value))
                bins[col] = min(lo, value), max(hi, value)
            commands = []
            for col, (lo, hi) in bins.items():
                y1 = top + height / 2 - hi / bound * height / 2
                y2 = top + height / 2 - lo / bound * height / 2
                commands.append(f'M{left+col},{y1:.2f}V{max(y2,y1+.35):.2f}')
            parts.append(f'<path d="{" ".join(commands)}" stroke="{color}" stroke-width="1" fill="none"/>')
        parts.append(f'<text x="{left}" y="{top+height+17}">0 s</text><text x="{left+width-58}" y="{top+height+17}">{duration:.2f} s</text>')
    parts.append('</g></svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--protocol", type=Path, default=ROOT / "data/splits/angles-2026-10-22/protocol.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/angles-2026-10-22")
    parser.add_argument("--audit-dir", type=Path, default=ROOT / "data/splits/angles-2026-10-22")
    args = parser.parse_args()
    report = preprocess(args.source_dir, args.protocol, args.output_dir, args.audit_dir)
    for name, info in report["outputs"].items():
        print(f"{name}: {info['samples']} rows, {info['included_samples']} included -> {info['path']}")


if __name__ == "__main__":
    main()
