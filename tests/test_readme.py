import html
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("generate_readme", ROOT / "scripts/generate_readme.py")
generate_readme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_readme)
from gallery import asset_name, build_gallery_manifest, load_gallery


class ReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = generate_readme.load_profile()
        cls.gallery = load_gallery()
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.text = (ROOT / "PROFILE.md").read_text(encoding="utf-8")

    def test_both_editions_match_their_generators(self):
        self.assertEqual(self.readme, generate_readme.render_readme(self.profile))
        self.assertEqual(self.text, generate_readme.render_text_profile(self.profile))

    def test_featured_work_precedes_labs_and_personal_record(self):
        names = [asset_name(key) for key in self.gallery["featured"] + self.gallery["lab"]]
        positions = [self.readme.index(name) for name in names]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(self.readme.index(asset_name("portfolio")), self.readme.index("systems-reel-v2.gif"))
        self.assertLess(self.readme.index(asset_name("zenith")), self.readme.index(asset_name("section-lab")))

    def test_opening_is_compact_and_links_to_readable_edition(self):
        opening = self.readme.split(asset_name("portfolio"), 1)[0]
        self.assertIn("PROFILE.md", opening)
        self.assertIn("Ayush_Roy_Resume_Public.pdf", opening)
        for old in ("identity-console", "proof-apps", "signal-strip", "systems-reel"):
            self.assertNotIn(old, opening)

    def test_every_authored_visible_block_and_link_remains_visual(self):
        no_comments = re.sub(r"<!--.*?-->", "", self.readme, flags=re.S)
        self.assertEqual(re.sub(r"<[^>]+>", "", no_comments).strip(), "")
        self.assertNotRegex(self.readme, r"(?m)^#{1,6}\s")
        self.assertEqual(re.findall(r"(?<!!)\[[^\]]+\]\([^)]+\)", self.readme), [])
        links = re.findall(r'<a href="[^"]+">.*?</a>', self.readme, re.S)
        self.assertTrue(links)
        self.assertTrue(all("<img " in link for link in links))
        for href in ("mailto:ayushroy.dev@gmail.com", self.profile["contact"]["linkedin"], self.profile["contact"]["steam"]):
            self.assertIn(href, self.readme)

    def test_images_have_semantic_alts_and_bounded_controls(self):
        for tag in re.findall(r"<img\b[^>]*>", self.readme):
            self.assertRegex(tag, r'alt="[^"]+"')
            self.assertRegex(tag, r'width="(?:100%|140|180|280)"')
        self.assertNotIn("TOTAL+PROFILE+VIEWS", self.readme)
        self.assertIn("label=PROFILE+VIEWS", self.readme)
        self.assertIn("not a unique-visitor", self.readme)

    def test_disclosures_and_section_navigation_are_native(self):
        targets = re.findall(r'<a href="#([^"]+)"', self.readme)
        anchors = re.findall(r'<a id="([^"]+)"', self.readme)
        self.assertEqual(len(anchors), len(set(anchors)))
        self.assertTrue(set(targets).issubset(anchors))
        self.assertEqual(self.readme.count("<details>"), len(self.profile["projects"]) + 1)
        self.assertEqual(self.readme.count("<details>"), self.readme.count("</details>"))
        self.assertNotIn("<details open", self.readme)
        for project in self.profile["projects"]:
            self.assertIn(f'Under the hood: {html.escape(project["name"], quote=True)}', self.readme)
        self.assertIn('media="(prefers-reduced-motion: reduce)"', self.readme)

    def test_only_expected_published_assets_are_referenced(self):
        referenced = set(re.findall(r"/output/([a-z0-9-]+\.(?:svg|gif|png))", self.readme))
        expected = {"hero.svg", *build_gallery_manifest(self.profile), *generate_readme.DYNAMIC_ASSETS, *generate_readme.MOTION_ASSETS}
        self.assertEqual(referenced, expected)

    def test_all_projects_have_source_controls_and_responsive_notes(self):
        for project in self.profile["projects"]:
            key = project["id"]
            spec = self.gallery["projects"][key]
            block = "\n".join(generate_readme.project_block(project, "yorayriniwnl", self.gallery))
            self.assertIn(project["repo"], block)
            self.assertIn(asset_name(key, True), block)
            self.assertIn(asset_name("dossier-" + key, True), block)
            if not spec["show_site"] and project.get("live"):
                self.assertNotIn('href="' + project["live"], block)

    def test_text_edition_is_complete_selectable_and_motion_free(self):
        self.assertNotIn("<img", self.text)
        self.assertNotIn("![", self.text)
        self.assertIn("# Ayush Roy", self.text)
        for project in self.profile["projects"]:
            self.assertIn(project["name"], self.text)
            for proof in project["proof"]:
                self.assertIn(proof, self.text)
        for items in self.profile["skills"].values():
            for skill in items:
                self.assertIn(skill, self.text)
        self.assertIn("earlier portfolio iteration", self.text)
        self.assertIn("not an end-to-end certification", self.text)

    def test_public_record_links_to_selectable_source_data(self):
        for filename in ("public-record.json", "contribution-record.json"):
            self.assertIn("/blob/output/" + filename, self.readme)
            self.assertIn("/blob/output/" + filename, self.text)

    def test_public_content_omits_private_and_retired_claims(self):
        for copy in (self.readme, self.text):
            for term in ("cgpa", "7.00/10", "yorayriniwnl@gmail.com", "4,000 GPU"):
                self.assertNotIn(term.lower(), copy.lower())
            self.assertIsNone(re.search(r"(?:\+?91[\s.-]?)?[6-9]\d{4}[\s.-]?\d{5}", copy))
        self.assertIn("Express", self.text)
        self.assertIn("Socket.IO", self.text)


if __name__ == "__main__":
    unittest.main()
