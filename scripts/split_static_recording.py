"""Partition an untouched phyphox export using its START/PAUSE metadata.

This is an inventory/split utility, not a rest detector or calibration pipeline.
Only the Python standard library is required. See data/README.md for usage.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
HEADERS = [
    "Time (s)",
    "Acceleration x (m/s^2)",
    "Acceleration y (m/s^2)",
    "Acceleration z (m/s^2)",
    "Absolute acceleration (m/s^2)",
]
PROVENANCE = ["source_row", "segment_id", "pose_observed", "repeat", "split"]
POSES = {"+X", "-X", "+Y", "-Y", "+Z", "-Z"}


def read_intervals(path: Path) -> list[dict]:
    """Use acquisition events, never guessed 30-second cuts or wall-clock gaps."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"event", "experiment time", "system time", "system time text"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("time.csv is missing required event/time columns")
        events = list(reader)
    if not events or len(events) % 2:
        raise ValueError("Expected complete START/PAUSE event pairs")
    intervals = []
    previous_wall_end = -math.inf
    for index in range(0, len(events), 2):
        start, stop = events[index:index + 2]
        if (start["event"], stop["event"]) != ("START", "PAUSE"):
            raise ValueError("Expected alternating START and PAUSE events")
        lo, hi = float(start["experiment time"]), float(stop["experiment time"])
        wall_lo, wall_hi = float(start["system time"]), float(stop["system time"])
        if not all(math.isfinite(x) for x in (lo, hi, wall_lo, wall_hi)):
            raise ValueError("Nonfinite event timestamp")
        if lo < 0 or hi <= lo or wall_hi <= wall_lo or wall_lo < previous_wall_end:
            raise ValueError("Invalid or overlapping acquisition interval")
        if intervals and lo < intervals[-1]["end_s"]:
            raise ValueError("Overlapping experiment-time intervals")
        intervals.append({
            "segment_id": len(intervals) + 1,
            "start_s": lo,
            "end_s": hi,
            "duration_s": hi - lo,
            "wall_start": start["system time text"],
            "wall_end": stop["system time text"],
            "pause_before_s": None if not intervals else wall_lo - previous_wall_end,
        })
        previous_wall_end = wall_hi
    return intervals


def read_samples(path: Path) -> tuple[list[list[str]], list[list[float]]]:
    """Validate exported fields while retaining every original numeric string."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.reader(stream)
        if next(reader, None) != HEADERS:
            raise ValueError("Unexpected acceleration CSV headers/units")
        rows = list(reader)
    if not rows:
        raise ValueError("Empty acceleration export")
    samples = []
    previous = -math.inf
    for number, row in enumerate(rows, 1):
        if len(row) != len(HEADERS):
            raise ValueError(f"Wrong column count at source data row {number}")
        sample = [float(value) for value in row]
        if not all(math.isfinite(value) for value in sample):
            raise ValueError(f"Nonfinite value at source data row {number}")
        if sample[0] <= previous:
            raise ValueError(f"Nonincreasing time at source data row {number}")
        previous = sample[0]
        samples.append(sample)
    return rows, samples


def observed_pose(median: list[float]) -> str:
    """Dominant measured axis only; this does not certify true support alignment."""
    order = sorted(range(3), key=lambda axis: abs(median[axis]), reverse=True)
    axis, runner_up = order[:2]
    if abs(median[axis]) == 0 or abs(median[axis]) < 3 * abs(median[runner_up]):
        raise ValueError("No clearly dominant measured axis for this interval")
    return ("+" if median[axis] > 0 else "-") + "XYZ"[axis]


def partition(samples: list[list[float]], intervals: list[dict]) -> list[list[int]]:
    """Assign all rows once, using half-open [START, PAUSE) intervals."""
    times = [sample[0] for sample in samples]
    groups = []
    covered = 0
    for interval in intervals:
        first = bisect.bisect_left(times, interval["start_s"])
        end = bisect.bisect_left(times, interval["end_s"])
        if first != covered or end == first:
            raise ValueError("Empty interval or samples outside acquisition events")
        groups.append(list(range(first, end)))
        covered = end
    if covered != len(samples):
        raise ValueError("Samples remain outside acquisition events")
    return groups


def describe(samples: list[list[float]], intervals: list[dict], groups: list[list[int]]) -> list[dict]:
    if len(intervals) != 12:
        raise ValueError("This six-face protocol requires exactly twelve recordings")
    result = []
    for interval, indices in zip(intervals, groups):
        axes = [[samples[i][axis] for i in indices] for axis in (1, 2, 3)]
        median = [statistics.median(values) for values in axes]
        result.append({
            **interval,
            "pose_observed": observed_pose(median),
            "samples": len(indices),
            "first_source_row": indices[0] + 1,
            "last_source_row": indices[-1] + 1,
            "first_sample_s": samples[indices[0]][0],
            "last_sample_s": samples[indices[-1]][0],
            "median_xyz_m_s2": median,
            "std_xyz_m_s2": [statistics.pstdev(values) for values in axes],
        })
    seen = set()
    for first in range(0, 12, 2):
        pair = result[first:first + 2]
        pose = pair[0]["pose_observed"]
        if pair[1]["pose_observed"] != pose or pose in seen:
            raise ValueError("Expected six distinct poses, each repeated consecutively")
        seen.add(pose)
        for repeat, segment in enumerate(pair, 1):
            segment.update(repeat=repeat, split="training" if repeat == 1 else "testing")
    if seen != POSES:
        raise ValueError("Missing one or more signed axis poses")
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def split_export(source_dir: Path, output_dir: Path, audit_dir: Path) -> dict:
    source_dir, output_dir, audit_dir = [p.resolve() for p in (source_dir, output_dir, audit_dir)]
    raw_root = ROOT / "data/raw"
    for destination in (output_dir, audit_dir):
        if destination == source_dir or destination.is_relative_to(source_dir) or destination == raw_root or destination.is_relative_to(raw_root):
            raise ValueError("Derived outputs must stay outside the raw recording directory")
    if output_dir == audit_dir or output_dir.is_relative_to(audit_dir) or audit_dir.is_relative_to(output_dir):
        raise ValueError("Use separate output and audit directories")
    raw = source_dir / "Raw Data.csv"
    event_file = source_dir / "meta/time.csv"
    sources = [raw, event_file]
    device_file = source_dir / "meta/device.csv"
    if device_file.exists():
        sources.append(device_file)
    hashes = {display_path(path): sha256(path) for path in sources}
    intervals = read_intervals(event_file)
    rows, samples = read_samples(raw)
    groups = partition(samples, intervals)
    segments = describe(samples, intervals, groups)
    # All validation precedes output creation. No filtering, fitting or resampling.
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for split in ("training", "testing"):
        path = output_dir / f"{split}.csv"
        count = 0
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(HEADERS + PROVENANCE)
            for segment, indices in zip(segments, groups):
                if segment["split"] != split:
                    continue
                for i in indices:
                    writer.writerow(rows[i] + [i + 1, segment["segment_id"], segment["pose_observed"], segment["repeat"], split])
                    count += 1
        outputs[split] = {"path": display_path(path), "samples": count, "sha256": sha256(path)}
    fields = ["segment_id", "pose_observed", "repeat", "split", "start_s", "end_s", "duration_s", "samples", "first_source_row", "last_source_row"]
    with (audit_dir / "segments.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(segments)
    report = {
        "schema_version": 1,
        "source_sha256": hashes,
        "policy": "First complete recording of each consecutive pose pair trains; second tests. No random sample split.",
        "boundary_convention": "[START, PAUSE), from meta/time.csv experiment time; wall-clock pauses are excluded by phyphox.",
        "source_row_convention": "1-based data row, excluding the CSV header (physical line = source_row + 1).",
        "pose_convention": "Dominant signed measured component from each complete recording's median; not an independent orientation measurement. Dominance >= 3 times the next component is an inventory guard, not a rest threshold.",
        "preprocessing": "None. All rows and original five numeric strings retained; output adds provenance columns only.",
        "ready_for_fitting": False,
        "limitations": [
            "First/second repeats come from one exported collection session, not independent sessions A/B.",
            "Pause events alone do not establish that the phone was repositioned between same-pose repeats.",
            "Support alignment, case configuration and user-selected sampling setting are unconfirmed.",
            "Rest masks, independent ramp angles, limit experiments and calibration are pending.",
        ],
        "audit": {
            "samples": len(samples),
            "acquisition_duration_s": sum(s["duration_s"] for s in segments),
            "median_sample_interval_s": statistics.median(b[0] - a[0] for a, b in zip(samples, samples[1:])),
            "max_sample_interval_s": max(b[0] - a[0] for a, b in zip(samples, samples[1:])),
            "nonfinite_values": 0,
            "nonincreasing_timestamps": 0,
            "unassigned_samples": 0,
            "max_exported_magnitude_difference_m_s2": max(abs(math.hypot(*s[1:4]) - s[4]) for s in samples),
        },
        "outputs": outputs,
        "segments": segments,
    }
    if any(sha256(path) != hashes[display_path(path)] for path in sources):
        raise ValueError("A source file changed during splitting; discard derived outputs and rerun")
    (audit_dir / "manifest.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = [
        "# Static recording split: 21 October 2026", "",
        "Twelve START/PAUSE recordings confirm two consecutive repeats of each signed axis. Labels describe the dominant **measured** component, not independently verified reference alignment.", "",
        "| Run | Observed pose | Assignment | Duration (s) | Samples | Source data rows |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for s in segments:
        lines.append(f"| {s['segment_id']} | {s['pose_observed']} | {s['split']} | {s['duration_s']:.3f} | {s['samples']:,} | {s['first_source_row']}-{s['last_source_row']} |")
    lines += [
        "",
        f"Training: **{outputs['training']['samples']:,} samples**. Testing: **{outputs['testing']['samples']:,} samples**. All **{len(samples):,}** source samples are assigned exactly once, with no overlap or omitted rows.",
        "",
        "The first five fields retain the original numeric strings and experiment timestamps. Added columns identify the source data row, acquisition run, observed pose, repeat and split. Source data row 1 is physical CSV line 2. No trimming, smoothing, resampling, fitting or error-based selection was performed.",
        "",
        "`manifest.json` records source/output SHA-256 hashes, exact event boundaries, wall-clock acquisition times, descriptive medians/standard deviations and checks. `segments.csv` provides a compact boundary table. The training/testing CSVs in `data/processed/static-2026-10-21/` are versioned at the user's request; regenerate them using the command in `data/README.md`. Git preserves their exact bytes so hashes also match in a fresh checkout.",
        "",
        f"The raw CSV has strictly increasing finite timestamps and finite acceleration values. Maximum absolute difference between the exported magnitude and the vector norm: {report['audit']['max_exported_magnitude_difference_m_s2']:.3g} m/s². These inventory checks do not certify metrological accuracy or establish that every sample is stationary.",
        "",
        "## Before calibration", "",
        "These are within-session repeat holdouts, not independent collection sessions. In particular, pauses do not prove independent repositioning. Keep the assignment fixed, tune future preprocessing on training only, and use independently measured ramps as additional holdout validation. Confirm support alignment, case and sampling settings. Implement and review rest masks before fitting. Ramp recordings and a referenced limit experiment remain pending.", "",
    ]
    (audit_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="Export directory containing Raw Data.csv and meta/time.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/static-2026-10-21")
    parser.add_argument("--audit-dir", type=Path, default=ROOT / "data/splits/static-2026-10-21")
    args = parser.parse_args()
    try:
        report = split_export(args.source_dir, args.output_dir, args.audit_dir)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Split failed: {error}\n")
    for split, output in report["outputs"].items():
        print(f"{split}: {output['samples']:,} samples -> {output['path']}")
    print(f"Audit: {display_path(args.audit_dir / 'README.md')}")
    print("Untrimmed repeats only; independent ramps, preprocessing and fitting remain pending.")


if __name__ == "__main__":
    main()
