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
        self.assertIn("365 DAYS / CONTRIBUTIONS", svg)
        self.assertNotIn("AUTO-REFRESH // 24H", svg)
        self.assertIn("prefers-reduced-motion: reduce", svg)
        self.assertIn("stroke-dashoffset", svg)
        self.assertIn("data-date=", svg)
        for mobile in (False, True):
            root=ET.fromstring(generate_contributions.build_contribution_stream_svg(days,mobile=mobile))
            cells=[el for el in root.iter() if el.get('data-date')]
            self.assertEqual(len(cells),365)
            self.assertEqual(sum(int(cell.get('data-count')) for cell in cells),sum(day['count'] for day in days))

    def test_metrics_use_exact_daily_counts(self):
        days = [
            {"date": generate_contributions.dt.date(2026, 8, 27), "count": 2, "level": 1},
            {"date": generate_contributions.dt.date(2026, 8, 28), "count": 7, "level": 3},
            {"date": generate_contributions.dt.date(2026, 8, 29), "count": 0, "level": 0},
        ]

        metrics = generate_contributions.contribution_metrics(days)

        self.assertEqual(metrics, {"total": 9, "active": 2, "longest": 2, "peak": 7})


if __name__ == "__main__":
    unittest.main()
