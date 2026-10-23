"""Model structures, frozen-artifact handling, export reading and linearity-test power."""
import csv
import json

import numpy as np
import pytest

from calib import AffineCalibration
from calib.analysis import freeze_or_verify
from calib.data import HEADERS, read_export
from calib.evidence import REFERENCES, leave_one_face_out, nearest_face_deg, rank_examples

G = 9.81
FACES = np.concatenate([np.eye(3) * G, -np.eye(3) * G])


def test_fitted_flag_is_explicit_and_never_promoted_by_metadata(tmp_path):
    unverified = AffineCalibration(np.eye(3), np.zeros(3), {"source": "someone else's notes"})
    path = tmp_path / "unverified.json"
    unverified.save(path)
    assert json.loads(path.read_text())["fitted"] is False
    restored = AffineCalibration.load(path)
    assert restored.fitted is False and restored.to_dict()["fitted"] is False
    assert AffineCalibration.fit(FACES, FACES, {"files": ["synthetic"]}).fitted is True
    with pytest.raises(ValueError, match="provenance"):
        AffineCalibration(np.eye(3), np.zeros(3), None, fitted=True)
    path.write_text(path.read_text().replace('"fitted": false', '"fitted": "yes"'))
    with pytest.raises(ValueError, match="fitted"):
        AffineCalibration.load(path)


def test_six_position_fit_recovers_gains_and_ignores_placement_tilt():
    S, b = np.diag([1.02, .97, 1.01]), np.array([.11, -.07, .05])
    measured = FACES @ S.T + b
    # A 1 degree support tilt on the positive faces only (like a camera bump):
    # perpendicular components change at first order, axial ones only at second order.
    tilted = measured.copy()
    for j in range(3):
        tilted[j, (j + 1) % 3] += G * np.radians(1)
    six = AffineCalibration.fit(FACES, tilted, {"files": ["synthetic"]}, structure="diagonal")
    np.testing.assert_allclose(six.S, S, atol=1e-12)
    np.testing.assert_allclose(six.b, b, atol=1e-12)
    full = AffineCalibration.fit(FACES, tilted, {"files": ["synthetic"]})
    # The full model turns the placement tilt into spurious cross-axis coupling.
    assert np.max(np.abs(full.S - np.diag(np.diag(full.S)))) > .008
    assert six.diagnostics["structure"] == "diagonal" and six.diagnostics["parameters"] == 6


def test_six_position_requires_both_faces_of_every_axis():
    with pytest.raises(ValueError, match="rank 2"):
        AffineCalibration.fit(FACES[:5], FACES[:5], {"files": ["synthetic"]}, structure="diagonal")
    with pytest.raises(ValueError, match="structure"):
        AffineCalibration.fit(FACES, FACES, {"files": ["synthetic"]}, structure="quadratic")
    assert rank_examples() == {"all six faces": 4, "four faces +X,+Y,+Z,-X": 4, "planar +/-X, +/-Y": 3,
                               "three faces +X,+Y,+Z": 3, "one pose repeated": 1}


def test_leave_one_face_out_is_exact_for_affine_data_and_flags_unidentifiable_models():
    S = np.array([[1.01, .01, -.02], [.0, .98, .03], [.01, -.01, 1.02]])
    measured = REFERENCES @ S.T + [.1, -.2, .05]  # analysis pose order: +X, -X, +Y, -Y, +Z, -Z
    rows, summary = leave_one_face_out(measured, "full")
    assert summary["identifiable_folds"] == 6 and summary["vector_rmse_m_s2"] < 1e-12
    rows, summary = leave_one_face_out(measured, "diagonal")
    assert summary["identifiable_folds"] == 0 and all("rank 2" in r["reason"] for r in rows)


def test_magnitude_test_detects_nonproportional_scaling_but_not_linear_sensors():
    """|a_hat| = g at intermediate orientations has power against a 0.5 % compression."""
    angles = np.radians([15, 30, 45])
    intermediate = np.array([[0, G * np.sin(a), G * np.cos(a)] for a in angles])
    linear = lambda a: a @ np.diag([1.02, .99, 1.01]).T + [.1, -.05, .02]
    compressed = lambda a: linear(a) - .05 * G * (a / G) ** 3 + .05 * G * (a / G)  # exact at +/-g only
    for sensor, expect_large in ((linear, False), (compressed, True)):
        model = AffineCalibration.fit(FACES, sensor(FACES), {"files": ["synthetic"]}, structure="diagonal")
        error = np.abs(np.linalg.norm(model.apply(sensor(intermediate)), axis=1) - G)
        assert bool(error.max() > .04) == expect_large, error
    np.testing.assert_allclose(nearest_face_deg(intermediate), [15, 30, 45])


def test_frozen_artifacts_are_verified_not_rewritten(tmp_path):
    path = tmp_path / "fit.json"
    value = {"S": [[1.0, 0.0], [0.0, 1.0]], "b": [0.1, 0.2], "fitted": True, "name": "x"}
    assert freeze_or_verify(path, value) == "written"
    assert b"\r" not in path.read_bytes()
    # A Windows-written archive (CRLF) with last-digit float noise still verifies, byte-for-byte untouched.
    path.write_bytes(json.dumps(value, indent=2).replace("\n", "\r\n").encode())
    archived = path.read_bytes()
    assert freeze_or_verify(path, {**value, "b": [0.1 + 1e-15, 0.2]}) == "verified"
    assert path.read_bytes() == archived
    with pytest.raises(ValueError, match="differ"):
        freeze_or_verify(path, {**value, "b": [0.11, 0.2]})
    with pytest.raises(ValueError, match="differ"):
        freeze_or_verify(path, {**value, "fitted": False})
    assert freeze_or_verify(path, {**value, "b": [0.11, 0.2]}, refreeze=True) == "written"


def write_export(folder, times, events):
    (folder / "meta").mkdir(parents=True)
    with (folder / "Raw Data.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(HEADERS)
        for t in times:
            writer.writerow([f"{t:.9E}", "1.0E-2", "0", "9.81E0", "9.81E0"])
    with (folder / "meta/time.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["event", "experiment time", "system time", "system time text"])
        writer.writerows(events)


def test_raw_export_reader_uses_half_open_events_and_rejects_uncovered_samples(tmp_path):
    good = tmp_path / "good"
    write_export(good, [0, .5, 1, 1.5], [["START", 0, 0, ""], ["PAUSE", 1, 1, ""], ["START", 1, 2, ""], ["PAUSE", 2, 3, ""]])
    recording, intervals = read_export(good)
    assert recording.segment.tolist() == [1, 1, 2, 2] and sorted(intervals) == [1, 2]
    bad = tmp_path / "bad"
    write_export(bad, [0, .5, 1, 1.5], [["START", 0, 0, ""], ["PAUSE", 1, 1, ""]])
    with pytest.raises(ValueError, match="outside"):
        read_export(bad)
