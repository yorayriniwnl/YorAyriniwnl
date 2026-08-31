import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_contributions.py"
spec = importlib.util.spec_from_file_location("generate_contributions", SCRIPT)
generate_contributions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_contributions)


class GenerateContributionsTests(unittest.TestCase):
    def test_public_calendar_parser_extracts_exact_counts(self):
        source = """
        <td data-date="2026-08-27" id="day-a" data-level="0" class="ContributionCalendar-day"></td>
        <td data-date="2026-08-28" id="day-b" data-level="3" class="ContributionCalendar-day"></td>
        <tool-tip for="day-a">No contributions on August 27th.</tool-tip>
        <tool-tip for="day-b">17 contributions on August 28th.</tool-tip>
        """

        days = generate_contributions.parse_contribution_html(source)

        self.assertEqual(len(days), 2)
        self.assertEqual(days[0]["count"], 0)
        self.assertEqual(days[1]["count"], 17)
        self.assertEqual(days[1]["level"], 3)

    def test_sample_stream_is_valid_animated_svg(self):
        days = generate_contributions.sample_contributions()
        svg = generate_contributions.build_contribution_stream_svg(days)

        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertEqual(len(days), 365)
        self.assertIn("CONTRIBUTION SIGNAL // 365-DAY ACTIVITY", svg)
        self.assertIn("AUTO-REFRESH // 24H", svg)
        self.assertIn("stroke-dashoffset", svg)
        self.assertIn("data-date=", svg)

    def test_metrics_use_exact_daily_counts(self):
        days = [
            {"date": generate_contributions.dt.date(2026, 8, 27), "count": 2, "level": 1},
            {"date": generate_contributions.dt.date(2026, 8, 28), "count": 7, "level": 3},
            {"date": generate_contributions.dt.date(2026, 8, 29), "count": 0, "level": 0},
        ]

        metrics = generate_contributions.contribution_metrics(days)

        self.assertEqual(metrics, {"total": 9, "active": 2, "longest": 2, "peak": 7})

    def test_selectable_snapshot_matches_chart_counts(self):
        days = [
            {"date": generate_contributions.dt.date(2026, 8, 29), "count": 0},
            {"date": generate_contributions.dt.date(2026, 8, 27), "count": 2},
            {"date": generate_contributions.dt.date(2026, 8, 28), "count": 7},
        ]
        snapshot = generate_contributions.contribution_snapshot(days, "31 Aug 2026 / 06:00 UTC")
        self.assertEqual(snapshot["total"], 9)
        self.assertEqual(snapshot["active_days"], 2)
        self.assertEqual(snapshot["first_date"], "2026-08-27")
        self.assertEqual(snapshot["last_date"], "2026-08-29")
        self.assertEqual([item["count"] for item in snapshot["days"]], [2, 7, 0])
        self.assertFalse(snapshot["sample"])
        self.assertTrue(generate_contributions.contribution_snapshot(days, "preview", sample=True)["sample"])
        with self.assertRaises(ValueError):
            generate_contributions.contribution_snapshot([], "31 Aug 2026")


if __name__ == "__main__":
    unittest.main()
