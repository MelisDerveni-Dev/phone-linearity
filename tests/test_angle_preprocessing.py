"""Tests of event boundaries, held-out pairs, geometry and source preservation."""
import csv
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import preprocess_angles as prep


class AnglePreprocessingTests(unittest.TestCase):
    def test_geometry_and_invalid_contact_distances(self):
        self.assertAlmostEqual(prep.angle_degrees(.10, .16), 38.68218745348944)
        self.assertAlmostEqual(prep.angle_degrees(.05, .16), 18.20995686428301)
        for h, length in ((.1, 0), (.2, .16), (-.1, .16), (math.nan, .16), (.1, math.inf)):
            with self.subTest(h=h, length=length), self.assertRaises(ValueError):
                prep.angle_degrees(h, length)

    def test_half_open_timing_mask_does_not_move_event_boundaries(self):
        self.assertEqual(prep.boundary_mask([10, 10.9, 11, 14.99, 15, 15.9], 10, 16, 1),
                         [False, False, True, True, False, False])
        with self.assertRaises(ValueError):
            prep.boundary_mask([0], 0, 2, 1)

    def test_complete_partition_preservation_and_shaking_retention(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            raw = base / "raw"
            (raw / "meta").mkdir(parents=True)
            protocol = {"boundary_trim_s": 1, "contact_spacing_m": .16,
                        "runs": [{"pair_id": i // 2 + 1 if i < 8 else None,
                                  "kind": "ramp" if i < 8 else "shaking",
                                  "split": ("training" if i % 2 == 0 else "testing") if i < 8 else "limit",
                                  "height_m": (.1 if i < 4 else .05) if i < 8 else None} for i in range(9)]}
            config = base / "protocol.json"
            config.write_text(json.dumps(protocol))
            with (raw / "Raw Data.csv").open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(prep.HEADERS)
                for run in range(9):
                    for offset in (0, 1, 4, 5):
                        writer.writerow([f"{run*6+offset:.9E}", "0.000", "0", "9.81000", "9.81"])
            with (raw / "meta/time.csv").open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["event", "experiment time", "system time", "system time text"])
                for run in range(9):
                    writer.writerow(["START", run * 6, 100 + run * 10, "start"])
                    writer.writerow(["PAUSE", (run + 1) * 6, 106 + run * 10, "end"])
            (raw / "meta/device.csv").write_text("property,value\n")
            original = {p: p.read_bytes() for p in raw.rglob("*.csv")}
            with (raw / "Raw Data.csv").open(newline="") as stream:
                source_rows = list(csv.reader(stream))[1:]
            report = prep.preprocess(raw, config, base / "out", base / "audit")
            self.assertEqual(report["samples"], 36)
            ids = []
            for name, count, included in (("training", 16, 8), ("testing", 16, 8), ("limit", 4, 4)):
                self.assertEqual(report["outputs"][name]["samples"], count)
                self.assertEqual(report["outputs"][name]["included_samples"], included)
                with (base / "out" / f"{name}.csv").open(newline="") as stream:
                    data = list(csv.DictReader(stream))
                for row in data:
                    ids.append(int(row["source_row"]))
                    self.assertEqual([row[h] for h in prep.HEADERS], source_rows[int(row["source_row"]) - 1])
                    self.assertEqual(row["Acceleration z (m/s^2)"], "9.81000")
                    if name == "limit":
                        self.assertEqual(row["include"], "1")
                        self.assertEqual(row["angle_deg"], "")
                    else:
                        height = .1 if int(row["segment_id"]) <= 4 else .05
                        self.assertAlmostEqual(float(row["angle_deg"]), prep.angle_degrees(height, .16))
                self.assertEqual({int(row["segment_id"]) for row in data},
                                 {1, 3, 5, 7} if name == "training" else {2, 4, 6, 8} if name == "testing" else {9})
            self.assertEqual(sorted(ids), list(range(1, 37)))
            for p, content in original.items():
                self.assertEqual(p.read_bytes(), content)
            repeated = prep.preprocess(raw, config, base / "out", base / "audit")
            self.assertEqual(repeated, report)
            # Unknown geometry must not silently become a reference angle.
            protocol["contact_spacing_m"] = None
            config.write_text(json.dumps(protocol))
            pending = prep.preprocess(raw, config, base / "out", base / "audit")
            self.assertTrue(all(s["angle_deg"] is None for s in pending["segments"]))
            protocol["runs"][1]["height_m"] = .05
            config.write_text(json.dumps(protocol))
            with self.assertRaisesRegex(ValueError, "same specified height"):
                prep.preprocess(raw, config, base / "bad", base / "bad-audit")
            self.assertFalse((base / "bad").exists())


if __name__ == "__main__":
    unittest.main()
