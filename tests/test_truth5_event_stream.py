import csv
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "datagen" / "generate.py"


class TruthFiveEventStreamTests(unittest.TestCase):
    def test_rotterdam_gap_is_distinguishable_from_sibling_feeds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--output-dir",
                    temp_dir,
                    "--containers-per-day",
                    "120",
                ],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            event_path = Path(temp_dir) / "fact_container_event.csv"
            with event_path.open(encoding="utf-8", newline="") as source:
                events = list(csv.DictReader(source))

            counts = Counter(
                (row["source_system"], row["event_type"], row["event_at_utc"][:10])
                for row in events
            )
            affected_dates = ("2026-09-01", "2026-09-02", "2026-09-03")
            for event_date in affected_dates:
                self.assertEqual(counts[("TOS_ROTTERDAM", "GATE_OUT", event_date)], 0)
                for event_type in ("GATE_IN", "DISCHARGE", "LOAD"):
                    self.assertGreater(counts[("TOS_ROTTERDAM", event_type, event_date)], 0)
                sibling_gate_out = sum(
                    count
                    for (source_system, event_type, day), count in counts.items()
                    if source_system != "TOS_ROTTERDAM"
                    and event_type == "GATE_OUT"
                    and day == event_date
                )
                self.assertGreater(sibling_gate_out, 0)
                prior_sibling_gate_out = sum(
                    count
                    for (source_system, event_type, day), count in counts.items()
                    if source_system != "TOS_ROTTERDAM"
                    and event_type == "GATE_OUT"
                    and day == "2026-08-31"
                )
                self.assertGreater(sibling_gate_out, prior_sibling_gate_out * 0.7)
                self.assertLess(sibling_gate_out, prior_sibling_gate_out * 1.3)

            source_systems = {row["source_system"] for row in events}
            self.assertGreater(len(source_systems), 1)
            self.assertIn("TOS_SINGAPORE", source_systems)
            self.assertTrue(all(
                row["source_system"] == "TOS_ROTTERDAM"
                for row in events if row["port_code"] == "NLRTM"
            ))
            self.assertTrue(all(
                row["source_system"] == "TOS_SINGAPORE"
                for row in events if row["port_code"] == "SGSIN"
            ))

            grouped: dict[tuple[str, str], dict[str, datetime]] = {}
            for row in events:
                key = (row["container_id"], row["port_code"])
                grouped.setdefault(key, {})[row["event_type"]] = datetime.fromisoformat(
                    row["event_at_utc"]
                )
            complete_intervals = [
                (values["GATE_OUT"] - values["GATE_IN"]).total_seconds() / 3600
                for values in grouped.values()
                if "GATE_IN" in values and "GATE_OUT" in values
            ]
            self.assertTrue(complete_intervals)
            self.assertTrue(all(28 <= hours <= 32 for hours in complete_intervals))

            outage_gate_ins = [
                values["GATE_IN"]
                for (container_id, port_code), values in grouped.items()
                if port_code == "NLRTM"
                and "GATE_IN" in values
                and values["GATE_IN"].date().isoformat() in affected_dates
                and "GATE_OUT" not in values
            ]
            self.assertTrue(outage_gate_ins)
            snapshot = datetime.fromisoformat("2026-09-28T23:59:59+00:00")
            apparent_open_dwell = [
                min((snapshot - gate_in).total_seconds() / 3600, 72.0)
                for gate_in in outage_gate_ins
            ]
            self.assertEqual(min(apparent_open_dwell), 72.0)

            metadata_path = Path(temp_dir) / "dataset_metadata.csv"
            with metadata_path.open(encoding="utf-8", newline="") as source:
                metadata = list(csv.DictReader(source))
            self.assertEqual(metadata, [
                {"metadata_key": "DEMO_AS_OF", "metadata_value": "2026-09-28"},
                {"metadata_key": "GENERATOR_SEED", "metadata_value": "20260926"},
            ])

            journey_path = Path(temp_dir) / "fact_container_journey.csv"
            with journey_path.open(encoding="utf-8", newline="") as source:
                journey_columns = next(csv.reader(source))
            self.assertIn("seed_id", journey_columns)
            self.assertNotIn("reported_dwell_hours", journey_columns)
            self.assertNotIn("actual_dwell_hours", journey_columns)
            self.assertTrue((Path(temp_dir) / "truth_answer_key.csv").is_file())

        dwell_sql = (ROOT / "sql" / "02_curated_dwell.sql").read_text(encoding="utf-8")
        self.assertIn("LEAST(", dwell_sql)
        self.assertIn("72.0", dwell_sql)
        self.assertIn("PORTPILOT.RAW.DATASET_METADATA", dwell_sql)


if __name__ == "__main__":
    unittest.main()
