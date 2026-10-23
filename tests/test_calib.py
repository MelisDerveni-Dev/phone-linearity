"""Scientific recovery, bad inputs, stability/gap policy and frame tests."""
import csv
from pathlib import Path
import tempfile

import numpy as np
import pytest

from calib import AffineCalibration
from calib.analysis import slope_degrees
from calib.data import HEADERS, Recording, load_csv, retain_duration, rolling_variation, screen


def references():
    return np.concatenate([np.eye(3) * 9.81, -np.eye(3) * 9.81])


def test_known_cross_axis_affine_recovery_and_application():
    S = np.array([[1.04, .02, -.01], [-.03, .97, .04], [.01, -.02, 1.02]])
    b = np.array([.12, -.08, .05])
    ref = references()
    model = AffineCalibration.fit(ref, ref @ S.T + b, {"training_session": "synthetic"})
    np.testing.assert_allclose(model.S, S, atol=1e-13)
    np.testing.assert_allclose(model.b, b, atol=1e-13)
    # Held-out arbitrary vectors, not just fitted gravity faces.
    rng = np.random.default_rng(42)
    unseen = rng.normal(size=(30, 3)) * 12
    np.testing.assert_allclose(model.apply(unseen @ S.T + b), unseen, atol=1e-12)
    np.testing.assert_allclose(model.apply(b), [0, 0, 0], atol=1e-12)


def test_rank_deficiency_and_unusable_parameters_rejected():
    planar = references()[[0, 1, 3, 4]]
    with pytest.raises(ValueError, match="rank 4"):
        AffineCalibration.fit(planar, planar, {})
    for S in (np.zeros((3, 3)), np.diag([1, 1, 1e-12]), np.full((3, 3), np.nan)):
        with pytest.raises(ValueError):
            AffineCalibration(S, np.zeros(3))
    with pytest.raises(ValueError):
        AffineCalibration(np.eye(3), [0, 0, np.inf])


def test_json_roundtrip_and_units(tmp_path):
    model = AffineCalibration.fit(references(), references() * 1.02 + .1, {"files": ["synthetic"]})
    path = tmp_path / "params.json"
    model.save(path)
    restored = AffineCalibration.load(path)
    np.testing.assert_allclose(restored.apply([[0, 0, 9.81]]), model.apply([[0, 0, 9.81]]))
    path.write_text(path.read_text().replace('"m/s^2"', '"g"'))
    with pytest.raises(ValueError, match="units"):
        AffineCalibration.load(path)


def test_reader_rejects_nonfinite_duplicate_time_and_wrong_units(tmp_path):
    path = tmp_path / "recording.csv"
    def write(times, x="0", headers=HEADERS):
        with path.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(headers + ["source_row", "segment_id", "split"])
            for i, t in enumerate(times):
                writer.writerow([t, x, 0, 9.81, 9.81, i + 1, 1, "training"])
    write([0, .01, .02])
    assert load_csv(path).xyz.shape == (3, 3)
    for times, x in (([0, .01, .01], "0"), ([0, .01], "nan")):
        write(times, x)
        with pytest.raises(ValueError):
            load_csv(path)
    write([0, .01], headers=["Time (ms)"] + HEADERS[1:])
    with pytest.raises(ValueError, match="headers"):
        load_csv(path)


def test_stability_detects_disturbance_without_reference_error_selection():
    t = np.arange(0, 8, .01)
    xyz = np.tile([2., 3., 9.], (len(t), 1))  # Constant offset/tilt must not be rejected.
    xyz[(t >= 3) & (t < 3.4), 0] += np.sin(t[(t >= 3) & (t < 3.4)] * 80) * 2
    var = rolling_variation(t, xyz)
    included = retain_duration(t, (t >= 1) & (t < 7) & (var < .05))
    assert included[(t > 1.5) & (t < 2.5)].all()
    assert not included[(t > 3.05) & (t < 3.35)].any()
    assert included[(t > 5) & (t < 6)].all()
    # A gap must not join two short candidate intervals into one accepted interval.
    assert not retain_duration(np.array([0., .1, .2, 1.5, 1.6]), np.ones(5, bool)).any()


def test_policy_freezing_cannot_learn_on_test_data():
    t = np.arange(0, 5, .01)
    rec = Recording([{"split": "training"}] * len(t), t, np.tile([0., 0., 9.81], (len(t), 1)), np.ones(len(t), int))
    intervals = {1: {"start_s": 0, "end_s": 5}}
    mask, _, _, threshold = screen(rec, intervals)
    assert threshold == .05 and mask.any()
    rec.rows = [{"split": "testing"}] * len(t)
    with pytest.raises(ValueError, match="training only"):
        screen(rec, intervals)
    unchanged, _, _, _ = screen(rec, intervals, threshold)
    np.testing.assert_array_equal(unchanged, mask)


def test_unsigned_long_axis_slope_for_both_supports():
    theta = np.deg2rad(38.68218745348944)
    screen_up = [0, 9.81 * np.sin(theta), 9.81 * np.cos(theta)]
    on_side = [9.81 * np.cos(theta), 9.81 * np.sin(theta), 0]
    np.testing.assert_allclose(slope_degrees([screen_up, on_side]), [np.rad2deg(theta)] * 2)
