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
        self.assertIn("data:image/jpeg;base64,", svg)
        self.assertIn("AYR // OPERATOR ONLINE", svg)
        self.assertIn("FULL-STACK DEVELOPER", svg)
        self.assertIn('values="1492;1516;1492"', svg)

    def test_navigation_and_canonical_project_card_render_valid_svg(self):
        nav = generate_assets.build_nav_button_svg(
            "RÉSUMÉ", "VIEW PUBLIC RECORD", "▤", generate_assets.CONFIG, 42
        )
        project = next(
            item for item in generate_assets.PROFILE["projects"] if item["id"] == "vision"
        )
        card = generate_assets.build_project_card_svg(
            generate_assets.canonical_project_card_spec(project),
            generate_assets.CONFIG,
        )

        self.assertTrue(ET.fromstring(nav).tag.endswith("svg"))
        self.assertTrue(ET.fromstring(card).tag.endswith("svg"))
        self.assertIn("AI VS. REAL IMAGE DETECTOR", card)
        self.assertIn("78% HELD-OUT TEST ACCURACY", card.upper())
        self.assertIn("data:image/jpeg;base64,", card)

    def test_manifest_contains_only_public_readme_assets(self):
        manifest = generate_assets.build_asset_manifest()
        expected = {
            "hero.svg",
            "signal-strip.svg",
            "operator-gateway.svg",
            "achievement-rack.svg",
            "protocol-engineer.svg",
            "protocol-product.svg",
            "protocol-human.svg",
            "project-portfolio.svg",
            "project-helios.svg",
            "project-zenith.svg",
            "project-vision.svg",
            "project-talks.svg",
            "arsenal.svg",
            "finale.svg",
            "nav-portfolio.svg",
            "nav-projects.svg",
            "nav-resume.svg",
            "nav-linkedin.svg",
            "section-projects.svg",
            "section-arsenal.svg",
            "section-record.svg",
        }

        self.assertEqual(set(manifest), expected)
        self.assertLess(sum(len(svg.encode("utf-8")) for svg in manifest.values()), 2_500_000)
        self.assertNotIn("nav-steam.svg", manifest)
        self.assertNotIn("project-next.svg", manifest)
        self.assertNotIn("+18.4%", "".join(manifest.values()))

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
