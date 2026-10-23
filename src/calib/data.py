"""Strict processed-export reader and training-only signal stability policy."""
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HEADERS = ["Time (s)", "Acceleration x (m/s^2)", "Acceleration y (m/s^2)",
           "Acceleration z (m/s^2)", "Absolute acceleration (m/s^2)"]


@dataclass
class Recording:
    rows: list
    t: np.ndarray
    xyz: np.ndarray
    segment: np.ndarray


def load_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(HEADERS + ["source_row", "segment_id", "split"]).issubset(reader.fieldnames or []):
            raise ValueError("Missing exported SI-unit headers or provenance")
        rows = list(reader)
    if not rows:
        raise ValueError("Empty recording")
    values = np.array([[float(r[h]) for h in HEADERS] for r in rows])
    segment = np.array([int(r["segment_id"]) for r in rows])
    source = [int(r["source_row"]) for r in rows]
    if not np.isfinite(values).all() or np.any(np.diff(values[:, 0]) <= 0):
        raise ValueError("Nonfinite sample or nonincreasing timestamps")
    if len(set(source)) != len(source) or min(source) < 1 or min(segment) < 1:
        raise ValueError("Invalid/duplicate row provenance")
    # Segment IDs must be contiguous groups, not interleaved fragments.
    transitions = segment[np.r_[True, segment[1:] != segment[:-1]]]
    if len(np.unique(transitions)) != len(transitions):
        raise ValueError("Interleaved acquisition segments")
    return Recording(rows, values[:, 0], values[:, 1:4], segment)


def read_export(folder):
    """Read an unchanged phyphox export: Raw Data.csv plus meta/time.csv events.

    Returns a Recording whose segments are the half-open [START, PAUSE)
    acquisition intervals, and the interval table used by ``screen``.
    """
    folder = Path(folder)
    with (folder / "Raw Data.csv").open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        if next(reader, None) != HEADERS:
            raise ValueError("Unexpected acceleration CSV headers/units")
        values = np.array([[float(v) for v in row] for row in reader])
    if values.ndim != 2 or not len(values) or values.shape[1] != len(HEADERS) or not np.isfinite(values).all():
        raise ValueError("Empty, ragged or nonfinite acceleration export")
    if np.any(np.diff(values[:, 0]) <= 0):
        raise ValueError("Nonincreasing timestamps")
    with (folder / "meta/time.csv").open(encoding="utf-8-sig", newline="") as stream:
        events = list(csv.DictReader(stream))
    if not events or len(events) % 2 or any((a["event"], b["event"]) != ("START", "PAUSE") for a, b in zip(events[::2], events[1::2])):
        raise ValueError("Expected complete alternating START/PAUSE events")
    intervals, segment = {}, np.zeros(len(values), dtype=int)
    for k, (start, stop) in enumerate(zip(events[::2], events[1::2]), 1):
        lo, hi = float(start["experiment time"]), float(stop["experiment time"])
        if not lo < hi:
            raise ValueError("Invalid acquisition interval")
        ids = (values[:, 0] >= lo) & (values[:, 0] < hi)
        if not ids.any() or segment[ids].any():
            raise ValueError("Empty or overlapping acquisition interval")
        segment[ids] = k
        intervals[k] = {"segment_id": k, "start_s": lo, "end_s": hi}
    if not segment.all():
        raise ValueError("Samples remain outside acquisition events")
    rows = [{"source_row": i + 1, "segment_id": int(s), "split": "validation"} for i, s in enumerate(segment)]
    return Recording(rows, values[:, 0], values[:, 1:4], segment), intervals


def rolling_variation(t, xyz, window_s=.25, max_gap_s=.1):
    """RMS vector variation about a local mean; never distance from a target."""
    lo = np.searchsorted(t, t - window_s / 2, side="left")
    hi = np.searchsorted(t, t + window_s / 2, side="right")
    n = hi - lo
    total = np.vstack([np.zeros(3), np.cumsum(xyz, axis=0)])
    squared = np.r_[0., np.cumsum(np.sum(xyz * xyz, axis=1))]
    mean = (total[hi] - total[lo]) / n[:, None]
    variance = (squared[hi] - squared[lo]) / n - np.sum(mean * mean, axis=1)
    result = np.sqrt(np.maximum(variance, 0))
    gaps = np.r_[0, np.cumsum(np.diff(t) > max_gap_s)]
    valid = (n >= 3) & ((t[hi - 1] - t[lo]) >= .8 * window_s) & ((gaps[hi - 1] - gaps[lo]) == 0)
    return np.where(valid, result, np.inf)


def retain_duration(t, candidate, minimum_s=1., max_gap_s=.1):
    """Keep only continuous candidate intervals lasting at least one second."""
    result = np.zeros(len(t), dtype=bool)
    indices = np.flatnonzero(candidate)
    if not len(indices):
        return result
    cuts = np.flatnonzero((np.diff(indices) != 1) | (np.diff(t[indices]) > max_gap_s)) + 1
    for group in np.split(indices, cuts):
        if t[group[-1]] - t[group[0]] >= minimum_s:
            result[group] = True
    return result


def screen(recording, intervals, threshold=None):
    """Build all segment-local diagnostics before selecting training threshold."""
    variation = np.empty(len(recording.t))
    boundary = np.zeros(len(recording.t), dtype=bool)
    for segment in np.unique(recording.segment):
        ids = np.flatnonzero(recording.segment == segment)
        interval = intervals[int(segment)]
        t = recording.t[ids]
        variation[ids] = rolling_variation(t, recording.xyz[ids])
        boundary[ids] = (t >= interval["start_s"] + 1) & (t < interval["end_s"] - 1)
    if threshold is None:
        if {r["split"] for r in recording.rows} != {"training"}:
            raise ValueError("Stability threshold may be chosen on training only")
        quiet = variation[boundary & np.isfinite(variation)]
        if not len(quiet):
            raise ValueError("No eligible training stability windows")
        center = np.median(quiet)
        mad = np.median(np.abs(quiet - center))
        threshold = float(max(.05, center + 8 * 1.4826 * mad))
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("Invalid stability threshold")
    include = np.zeros(len(recording.t), dtype=bool)
    for segment in np.unique(recording.segment):
        ids = np.flatnonzero(recording.segment == segment)
        include[ids] = retain_duration(recording.t[ids], boundary[ids] & (variation[ids] <= threshold))
    return include, variation, boundary, threshold
