"""Split/provenance tests; runnable with unittest or pytest, without phone access."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("split_static", Path(__file__).resolve().parents[1] / "scripts/split_static_recording.py")
split = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(split)


class StaticSplitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.raw = self.base / "raw"
        (self.raw / "meta").mkdir(parents=True)
        self.csv = self.raw / "Raw Data.csv"
        self.events = self.raw / "meta/time.csv"
        with self.csv.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(split.HEADERS)
            for run in range(12):
                xyz = [0, 0, 0]
                xyz[run // 4] = 9.81 if run % 4 < 2 else -9.81
                # Exact start belongs to the new run; last sample precedes PAUSE.
                for offset in (0, .25, .5):
                    writer.writerow([f"{run + offset:.9E}", *xyz, 9.81])
        with self.events.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["event", "experiment time", "system time", "system time text"])
            for run in range(12):
                writer.writerow(["START", run, 1000 + run * 10, f"start-{run}"])
                writer.writerow(["PAUSE", run + 1, 1001 + run * 10, f"end-{run}"])

    def generate(self):
        return split.split_export(self.raw, self.base / "processed", self.base / "audit")

    def test_complete_repeat_holdout_preserves_strings_and_raw_hash(self):
        before = {p: p.read_bytes() for p in (self.csv, self.events)}
        report = self.generate()
        with self.csv.open(newline="") as stream:
            original = list(csv.reader(stream))[1:]
        identifiers = []
        for name, repeat in (("training", "1"), ("testing", "2")):
            with (self.base / "processed" / f"{name}.csv").open(newline="") as stream:
                rows = list(csv.reader(stream))[1:]
            self.assertEqual(len(rows), 18)
            self.assertEqual({row[7] for row in rows}, split.POSES)
            self.assertEqual({row[8] for row in rows}, {repeat})
            self.assertEqual({row[9] for row in rows}, {name})
            for row in rows:
                source_row = int(row[5])
                self.assertEqual(row[:5], original[source_row - 1])
                identifiers.append(source_row)
        self.assertEqual(sorted(identifiers), list(range(1, 37)))
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)
            self.assertEqual(report["source_sha256"][split.display_path(path)], hashlib.sha256(content).hexdigest())
        self.assertFalse(report["ready_for_fitting"])
        saved = json.loads((self.base / "audit/manifest.json").read_text())
        self.assertEqual(saved, report)
        self.generate()
        self.assertEqual((self.base / "audit/manifest.json").read_text(), json.dumps(report, indent=2) + "\n")

    def test_pause_boundary_and_unassigned_samples(self):
        intervals = [{"start_s": 0, "end_s": 1}, {"start_s": 1, "end_s": 2}]
        self.assertEqual(split.partition([[0], [.9], [1], [1.9]], intervals), [[0, 1], [2, 3]])
        with self.assertRaisesRegex(ValueError, "outside"):
            split.partition([[0], [.9], [2]], intervals)
        with self.assertRaisesRegex(ValueError, "outside"):
            split.partition([[0], [1]], [{"start_s": .1, "end_s": 2}])

    def test_rejects_mismatched_repeats_and_incomplete_protocol(self):
        intervals = split.read_intervals(self.events)
        _, samples = split.read_samples(self.csv)
        groups = split.partition(samples, intervals)
        for index in groups[1]:
            samples[index][1:4] = [0, 9.81, 0]
        with self.assertRaisesRegex(ValueError, "repeated consecutively"):
            split.describe(samples, intervals, groups)
        with self.assertRaisesRegex(ValueError, "twelve"):
            split.describe(samples, intervals[:-1], groups[:-1])

    def test_rejects_corrupt_samples_before_creating_outputs(self):
        for bad in ("nan", "inf", "-inf"):
            with self.subTest(value=bad):
                self.csv.write_text(",".join(split.HEADERS) + f"\n0,{bad},0,9.81,9.81\n")
                with self.assertRaisesRegex(ValueError, "Nonfinite"):
                    self.generate()
                self.assertFalse((self.base / "processed").exists())
        self.csv.write_text(",".join(split.HEADERS) + "\n0,0,0,9.81,9.81\n0,0,0,9.81,9.81\n")
        with self.assertRaisesRegex(ValueError, "Nonincreasing"):
            self.generate()

    def test_rejects_malformed_events_and_writing_into_raw(self):
        for content in (
            "event,experiment time,system time,system time text\nSTART,0,0,start\n",
            "event,experiment time,system time,system time text\nPAUSE,0,0,start\nSTART,1,1,stop\n",
            "event,experiment time,system time,system time text\nSTART,0,0,start\nPAUSE,nan,1,stop\n",
        ):
            self.events.write_text(content)
            with self.assertRaises(ValueError):
                split.read_intervals(self.events)
        with self.assertRaisesRegex(ValueError, "outside the raw"):
            split.split_export(self.raw, self.raw / "derived", self.base / "audit")


if __name__ == "__main__":
    unittest.main()
