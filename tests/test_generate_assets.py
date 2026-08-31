import hashlib
import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("generate_assets", ROOT / "scripts/generate_assets.py")
generate_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_assets)
from gallery import APPROVED_HERO_LF_SHA256, asset_name, assert_approved_hero, load_gallery


class GenerateAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = generate_assets.build_asset_manifest()
        cls.gallery = load_gallery()

    def test_approved_hero_is_byte_for_byte_unchanged(self):
        hero = self.manifest["hero.svg"]
        assert_approved_hero(hero)
        self.assertEqual(hashlib.sha256(hero.encode()).hexdigest(), APPROVED_HERO_LF_SHA256)
        self.assertIn('values="1492;1516;1492"', hero)
        self.assertNotIn("data-rotating-earth", hero)
        self.assertNotIn("data-live-graph", hero)
        with self.assertRaises(ValueError):
            assert_approved_hero(hero + "changed")

    def test_all_assets_are_well_formed_and_self_contained(self):
        for filename, svg in self.manifest.items():
            with self.subTest(asset=filename):
                root = ET.fromstring(svg)
                self.assertTrue(root.tag.endswith("svg"))
                self.assertNotIn("<script", svg)
                self.assertNotIn("<foreignObject", svg)
                for node in root.iter():
                    if node.tag.endswith("image"):
                        self.assertTrue(node.get("href", "").startswith("data:image/"))

    def test_budget_remains_below_original_limit(self):
        self.assertLess(sum(len(svg.encode()) for svg in self.manifest.values()), 2_500_000)

    def test_each_project_has_distinct_responsive_art_and_complete_notes(self):
        for project in generate_assets.PROFILE["projects"]:
            for mobile in (False, True):
                with self.subTest(project=project["id"], mobile=mobile):
                    self.assertIn(asset_name(project["id"], mobile), self.manifest)
                    svg = self.manifest[asset_name("dossier-" + project["id"], mobile)]
                    root = ET.fromstring(svg)
                    copy = " ".join(root.itertext())
                    self.assertIn(project["name"], copy)
                    for proof in project["proof"]:
                        self.assertIn(proof, copy)
                    self.assertIn(self.gallery["projects"][project["id"]]["evidence_note"], " ".join(copy.split()))
                    self.assertIn("Source review:", copy)
        self.assertNotEqual(self.manifest[asset_name("portfolio")], self.manifest[asset_name("portfolio", True)])

    def test_old_duplicate_panels_are_retired(self):
        for filename in ("identity-console.svg", "signal-strip.svg", "skills-matrix.svg", "arsenal.svg", "proof-apps.svg"):
            self.assertNotIn(filename, self.manifest)
        self.assertNotIn("+18.4%", "".join(self.manifest.values()))

    def test_new_assets_have_titles_descriptions_and_motion_fallback(self):
        for name, svg in self.manifest.items():
            if name == "hero.svg":
                continue
            with self.subTest(asset=name):
                root = ET.fromstring(svg)
                self.assertEqual(root.get("role"), "img")
                self.assertIn('aria-labelledby="title description"', svg)
                self.assertIn("prefers-reduced-motion:reduce", svg)
                self.assertIn("<title ", svg)
                self.assertIn("<desc ", svg)

    def test_body_type_has_a_mobile_minimum_not_just_a_source_size(self):
        for name, svg in self.manifest.items():
            if name == "hero.svg":
                continue
            root = ET.fromstring(svg)
            source_width = float(root.get("width"))
            rendered_width = 207 if root.get("data-layout") == "mobile" else 489
            for node in root.iter():
                if node.get("data-text-role") != "body":
                    continue
                with self.subTest(asset=name, copy=node.text):
                    effective = float(node.get("font-size")) * rendered_width / source_width
                    self.assertGreaterEqual(effective, 14)

    def test_svg_labels_stay_vertically_inside_their_panels(self):
        for name, svg in self.manifest.items():
            if name == "hero.svg":
                continue
            root = ET.fromstring(svg)
            for node in root.iter():
                if node.tag.endswith("text") and node.get("y"):
                    with self.subTest(asset=name, copy=node.text):
                        self.assertLess(float(node.get("y")), float(root.get("height")) - 5)


if __name__ == "__main__":
    unittest.main()
