import importlib.util
import unittest
import xml.etree.ElementTree as ET
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
        svg = generate_stats.build_stats_combined_svg(
            generate_stats.SAMPLE_OVERVIEW,
            generate_stats.SAMPLE_LANGS,
            generate_stats.SAMPLE_STREAK,
            generate_stats.b64_font("dm-mono-500.woff2"),
            generate_stats.b64_font("cormorant-garamond-600.woff2"),
        )

        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))


if __name__ == "__main__":
    unittest.main()
