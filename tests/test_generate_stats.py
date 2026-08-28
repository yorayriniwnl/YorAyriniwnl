import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_stats.py"
spec = importlib.util.spec_from_file_location("generate_stats", SCRIPT)
generate_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_stats)


class GenerateStatsTests(unittest.TestCase):
    def test_profile_view_counter_parser_preserves_exact_total(self):
        svg = '<svg aria-label="TOTAL PROFILE VIEWS: 12,345"><title>TOTAL PROFILE VIEWS: 12,345</title></svg>'

        self.assertEqual(generate_stats.parse_profile_views(svg), 12345)

    def test_language_percentages_include_hidden_languages_in_denominator(self):
        rows = generate_stats.language_percentages(
            [("Python", 50), ("TypeScript", 30), ("Rust", 20), ("CSS", 100)]
        )

        self.assertEqual(rows[0], ("Python", 50, 25.0))
        self.assertEqual(rows[1], ("TypeScript", 30, 15.0))
        self.assertAlmostEqual(sum(row[2] for row in rows), 100.0)

    def test_sample_stats_render_valid_svg(self):
        svg = generate_stats.build_stats_combined_svg(
            generate_stats.SAMPLE_OVERVIEW,
            generate_stats.SAMPLE_LANGS,
            generate_stats.SAMPLE_STREAK,
            generate_stats.b64_font("dm-mono-500.woff2"),
            generate_stats.b64_font("cormorant-garamond-600.woff2"),
        )

        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))

    def test_missing_streak_token_renders_system_status(self):
        panel = generate_stats.build_streak_panel(None)

        self.assertIn("SYSTEM STATUS", panel)
        self.assertIn("TIMEZONE", panel)
        self.assertIn("TS+PY", panel)
        self.assertIn("INTERNSHIPS", panel)
        self.assertNotIn("RUST", panel)
        self.assertNotIn("STATS_TOKEN", panel)

    def test_overview_panel_includes_profile_views(self):
        panel = generate_stats.build_overview_panel(
            {"views": 237, "public_repos": 25, "stars": 2, "followers": 1}
        )

        self.assertIn("PROFILE TELEMETRY", panel)
        self.assertIn("237", panel)
        self.assertIn("VIEWS", panel)


if __name__ == "__main__":
    unittest.main()
