import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_assets.py"
spec = importlib.util.spec_from_file_location("generate_assets", SCRIPT)
generate_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_assets)


class GenerateAssetsTests(unittest.TestCase):
    def test_cinematic_hero_is_self_contained_valid_svg(self):
        svg = generate_assets.build_cinematic_hero_svg(generate_assets.CONFIG)

        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("data:image/png;base64,", svg)
        self.assertIn("AYR // OPERATOR ONLINE", svg)

    def test_interactive_console_assets_render_valid_svg(self):
        nav = generate_assets.build_nav_button_svg(
            "PORTFOLIO", "ENTER THE SYSTEM", "◢", generate_assets.CONFIG, 42
        )
        card = generate_assets.build_project_card_svg(
            {
                "kind": "next",
                "code": "SYS-07",
                "domain": "OPEN CHANNEL",
                "title": "NEXT TRANSMISSION",
                "stack": "COLLABORATION · RESEARCH · OPEN SOURCE",
                "summary": "Bring the difficult problem. We'll build the system.",
            },
            generate_assets.CONFIG,
        )

        self.assertTrue(ET.fromstring(nav).tag.endswith("svg"))
        self.assertTrue(ET.fromstring(card).tag.endswith("svg"))
        self.assertIn("AWAITING THE NEXT HARD PROBLEM", card)


if __name__ == "__main__":
    unittest.main()
