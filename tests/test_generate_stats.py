import importlib.util
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_stats.py"
spec = importlib.util.spec_from_file_location("generate_stats", SCRIPT)
generate_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_stats)


class GenerateStatsTests(unittest.TestCase):
    def test_language_percentages_include_hidden_languages_in_denominator(self):
        rows = generate_stats.language_percentages(
            [("Python", 50), ("TypeScript", 30), ("Rust", 20), ("CSS", 100)]
        )

        self.assertEqual(rows[0], ("Python", 50, 25.0))
        self.assertEqual(rows[1], ("TypeScript", 30, 15.0))
        self.assertAlmostEqual(sum(row[2] for row in rows), 100.0)

    def test_sample_stats_render_valid_svg(self):
        from redline import record
        for mobile in (False, True):
            svg = record(generate_stats.SAMPLE_OVERVIEW, [], '05 Sep 2026 / 12:00 UTC', mobile)
            root = ET.fromstring(svg)
            self.assertTrue(root.tag.endswith('svg'))
            self.assertIn('SAMPLE / NO LIVE DATA', svg)
            self.assertNotIn('AUTO-REFRESH', svg)

    def test_live_record_displays_snapshot_time_and_proportions(self):
        from redline import record
        rows=generate_stats.language_percentages([('Python',50),('TypeScript',150)])
        svg=record({'followers':3,'public_repos':26,'stars':2},rows,'05 Sep 2026 / 12:00 UTC')
        self.assertIn('UPDATED / 05 Sep 2026 / 12:00 UTC',svg)
        self.assertIn('25.0%',svg)
        self.assertIn('75.0%',svg)

    def test_partial_language_fetch_does_not_publish_misleading_percentages(self):
        with patch.object(generate_stats, 'gh_rest', side_effect=TimeoutError):
            with self.assertRaises(RuntimeError):
                generate_stats.fetch_languages([{'name':'example'}],None)

    def test_missing_streak_token_renders_system_status(self):
        panel = generate_stats.build_streak_panel(None)

        self.assertIn("SYSTEM STATUS", panel)
        self.assertIn("TIMEZONE", panel)
        self.assertIn("TS+PY", panel)
        self.assertIn("INTERNSHIPS", panel)
        self.assertNotIn("RUST", panel)
        self.assertNotIn("STATS_TOKEN", panel)

    def test_overview_panel_keeps_live_views_as_single_source_of_truth(self):
        panel = generate_stats.build_overview_panel(
            {"public_repos": 25, "stars": 2, "followers": 1}
        )

        self.assertIn("PROFILE TELEMETRY", panel)
        self.assertIn("REPOS", panel)
        self.assertNotIn("VIEWS", panel)


if __name__ == "__main__":
    unittest.main()
