"""Four-run validation must preserve data and use a frozen model/policy."""
import csv
import json

import numpy as np
import pytest

from calib import AffineCalibration
from calib.data import HEADERS
import validate_new_angles as validation


@pytest.fixture
def acquisition(tmp_path):
    raw = tmp_path / "raw"
    (raw / "meta").mkdir(parents=True)
    heights = [0., .04, .08, .11]
    S = np.diag([1.03, .97, 1.01])
    bias = np.array([.03, -.08, .1])
    model = AffineCalibration(S, bias, {"stability_threshold_m_s2": .05, "training_session": "synthetic only"})
    calibration = tmp_path / "calibration.json"
    model.save(calibration)
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"stability_threshold_m_s2": .05}))
    protocol = tmp_path / "protocol.json"
    config = {"height_order_m": heights, "contact_spacing_m": .16, "support_orientation": "screen_up",
              "calibration_sha256": validation.sha256(calibration), "frozen_policy_sha256": validation.sha256(policy)}
    protocol.write_text(json.dumps(config))
    with (raw / "Raw Data.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(HEADERS)
        for run, h in enumerate(heights):
            ref = np.array([0., 9.81*h/.16, 9.81*np.sqrt(1-(h/.16)**2)])
            measured = S @ ref + bias
            for t in np.arange(0, 6, .01):
                writer.writerow([f"{run*6+t:.9E}", *[f"{v:.12E}" for v in measured], np.linalg.norm(measured)])
    with (raw / "meta/time.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["event", "experiment time", "system time", "system time text"])
        for run in range(4):
            writer.writerow(["START",run*6,100+run*10,"start"])
            writer.writerow(["PAUSE",(run+1)*6,106+run*10,"stop"])
    (raw / "meta/device.csv").write_text("property,value\n")
    return tmp_path, raw, protocol, calibration, policy


def run_fixture(acquisition):
    base, raw, protocol, calibration, policy = acquisition
    return validation.evaluate(raw, protocol, calibration, policy, base/"results", base/"audit", base/"processed")


def test_frozen_fit_recovers_unseen_angles_and_preserves_every_original_row(acquisition, monkeypatch):
    base, raw, protocol, calibration, policy = acquisition
    originals = {p: p.read_bytes() for p in [*raw.rglob("*.csv"), protocol, calibration, policy]}
    # Any fitting in the evaluation path is a test failure.
    def no_fit(*args, **kwargs):
        raise AssertionError("Validation must not fit parameters")
    monkeypatch.setattr(AffineCalibration, "fit", no_fit)
    result = run_fixture(acquisition)
    assert result["samples"] == 2400
    assert result["summary"]["corrected_tilt_rmse_deg"] < 1e-9
    assert result["summary"]["raw_tilt_rmse_deg"] > .1
    with (base/"processed/validation.csv").open(newline="") as stream:
        derived = list(csv.reader(stream))[1:]
    with (raw/"Raw Data.csv").open(newline="") as stream:
        original = list(csv.reader(stream))[1:]
    assert [row[:5] for row in derived] == original
    assert [int(row[5]) for row in derived] == list(range(1,2401))
    assert sum(r["included_samples"] for r in result["segments"]) == result["included_samples"]
    assert result["segments"][0]["reference_status"].startswith("nominal")
    for path, content in originals.items():
        assert path.read_bytes() == content


@pytest.mark.parametrize("which,error", [("calibration", "calibration hash"), ("policy", "policy hash")])
def test_changed_frozen_parameters_or_policy_are_rejected(acquisition, which, error):
    base, raw, protocol, calibration, policy = acquisition
    target = calibration if which == "calibration" else policy
    target.write_text(target.read_text()+"\n")
    with pytest.raises(ValueError, match=error):
        run_fixture(acquisition)
    assert not (base/"results").exists()


def test_incomplete_protocol_rejected_before_output_creation(acquisition):
    base, raw, protocol, calibration, policy = acquisition
    config = json.loads(protocol.read_text())
    config["height_order_m"] = [0,.04,.08]
    protocol.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="four"):
        run_fixture(acquisition)
    assert not (base/"processed").exists()
