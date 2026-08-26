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
        self.assertIn('values="1492;1516;1492"', svg)

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

    def test_operator_mode_assets_are_valid_and_complete(self):
        assets = {
            "gateway": generate_assets.build_operator_gateway_svg(generate_assets.CONFIG),
            "rack": generate_assets.build_achievement_rack_svg(generate_assets.CONFIG),
            "trace": generate_assets.build_protocol_engineer_svg(generate_assets.CONFIG),
            "forge": generate_assets.build_protocol_product_svg(generate_assets.CONFIG),
            "archive": generate_assets.build_protocol_human_svg(generate_assets.CONFIG),
        }

        for name, svg in assets.items():
            with self.subTest(asset=name):
                self.assertTrue(ET.fromstring(svg).tag.endswith("svg"))

        self.assertIn("INITIATE OPERATOR MODE", assets["gateway"])
        self.assertIn("ACHIEVEMENTS UNLOCKED", assets["rack"])
        self.assertIn("Architecture starts at the constraint", assets["trace"])
        self.assertIn("Make the difficult", assets["forge"])
        self.assertIn("GRIND. BUILD. REPEAT.", assets["archive"])


if __name__ == "__main__":
    unittest.main()
