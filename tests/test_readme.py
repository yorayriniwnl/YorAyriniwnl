import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
README_PATH = ROOT / "README.md"
SCRIPT = ROOT / "scripts" / "generate_readme.py"
spec = importlib.util.spec_from_file_location("generate_readme", SCRIPT)
generate_readme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_readme)


class ReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = generate_readme.load_profile()
        cls.readme = README_PATH.read_text(encoding="utf-8")

    def test_readme_matches_canonical_generator(self):
        self.assertEqual(self.readme, generate_readme.render_readme(self.profile))

    def test_primary_narrative_is_visual_and_proof_first(self):
        section_assets = [
            "section-projects.svg",
            "section-field.svg",
            "section-arsenal.svg",
            "section-record.svg",
            "section-operator.svg",
            "section-channel.svg",
        ]
        positions = [self.readme.index(asset) for asset in section_assets]

        self.assertEqual(positions, sorted(positions))
        self.assertLess(
            self.readme.index("section-projects.svg"),
            self.readme.index("section-operator.svg"),
        )
        for project_id in generate_readme.SELECTED_PROJECT_IDS:
            project = next(item for item in self.profile["projects"] if item["id"] == project_id)
            self.assertIn(project["name"], self.readme)
            for proof in project["proof"]:
                self.assertIn(proof, self.readme)

    def test_every_visible_authored_block_is_visual(self):
        without_comments = re.sub(r"<!--.*?-->", "", self.readme, flags=re.DOTALL)
        visible_text = re.sub(r"<[^>]+>", "", without_comments).strip()

        self.assertEqual(visible_text, "")
        self.assertNotIn("<h1", self.readme)
        self.assertNotRegex(self.readme, r"(?m)^#{1,6}\s")
        self.assertNotRegex(self.readme, r"(?m)^\s*[-*+]\s+")
        self.assertRegex(
            self.readme,
            r"<summary><picture><img\b[^>]+></picture></summary>",
        )

    def test_layout_is_mobile_safe_and_images_are_accessible(self):
        image_tags = re.findall(r"<img\b[^>]*?/>", self.readme)
        widths = re.findall(r'width="([^"]+)"', self.readme)

        self.assertGreaterEqual(len(image_tags), 59)
        self.assertTrue(all(re.search(r'alt="[^"]+"', tag) for tag in image_tags))
        self.assertTrue(all(width in {"100%", "350", "240", "160"} for width in widths))
        self.assertNotIn('width="24%"', self.readme)
        self.assertNotIn('width="49%"', self.readme)
        self.assertIn("https://komarev.com/ghpvc/?", self.readme)
        self.assertIn("label=TOTAL+PROFILE+VIEWS", self.readme)
        self.assertIn("systems-reel.gif", self.readme)
        self.assertIn("systems-reel-mobile.gif", self.readme)
        self.assertIn("systems-reel-still.png", self.readme)
        self.assertIn("systems-reel-mobile-still.png", self.readme)
        self.assertNotIn("kinetic-primer.gif", self.readme)
        self.assertIn("skills-matrix.svg?rev=atlas-v1", self.readme)
        self.assertIn("field-notes.svg?rev=atlas-v1", self.readme)
        for filename in generate_readme.ATLAS_ASSETS:
            self.assertIn(f"output/{filename}?rev=atlas-v1", self.readme)
        for filename in generate_readme.MOTION_ASSETS:
            self.assertIn(f"output/{filename}?rev=motion-v3", self.readme)
        self.assertNotIn("github-readme-activity-graph", self.readme)
        for filename in generate_readme.PROJECT_VISUALS.values():
            self.assertRegex(
                self.readme,
                rf'output/{re.escape(filename)}(?:\?rev=[^" ]+)?" width="100%"',
            )

    def test_every_authored_hyperlink_is_a_visual_control(self):
        markdown_links = re.findall(r"(?<!!)\[[^\]]+\]\([^)]+\)", self.readme)
        html_links = re.findall(r'<a href="[^"]+">.*?</a>', self.readme, re.DOTALL)

        self.assertEqual(markdown_links, [])
        self.assertGreaterEqual(len(html_links), 30)
        self.assertTrue(all("<img " in link for link in html_links))
        for filename in (
            "nav-live.svg",
            "nav-source.svg",
            "nav-experiment.svg",
            "nav-email.svg",
            "nav-github.svg",
            "nav-devpost.svg",
            "nav-steam.svg",
        ):
            self.assertIn(f"output/{filename}", self.readme)

    def test_section_shortcuts_resolve_and_dossiers_remain_native(self):
        targets = re.findall(r'<a href="#([^"]+)"', self.readme)
        anchors = re.findall(r'<a id="([^"]+)"', self.readme)
        self.assertEqual(len(anchors), len(set(anchors)))
        self.assertEqual(set(targets), set(anchors))
        self.assertEqual(set(anchors), {"selected-systems", "field-notes", "public-record", "open-channel"})
        self.assertEqual(self.readme.count("<details>"), len(generate_readme.SELECTED_PROJECT_IDS) + 1)
        self.assertEqual(self.readme.count("<details>"), self.readme.count("</details>"))
        self.assertNotIn("<details open", self.readme)
        self.assertIn('media="(max-width: 600px) and (prefers-reduced-motion: reduce)"', self.readme)
        self.assertIn('media="(prefers-reduced-motion: reduce)"', self.readme)

    def test_public_content_is_current_and_privacy_safe(self):
        lower = self.readme.lower()

        self.assertIn("mailto:ayushroy.dev@gmail.com", lower)
        self.assertIn("ayush_roy_resume_public.pdf", lower)
        self.assertNotIn("yorayriniwnl@gmail.com", lower)
        self.assertNotIn("prisma", lower)
        self.assertNotIn("deep learning", lower)
        self.assertNotIn("convolutional neural network", lower)
        self.assertIsNone(re.search(r"(?:\+?91[\s.-]?)?[6-9]\d{4}[\s.-]?\d{5}", self.readme))

    def test_readme_references_only_published_visual_assets(self):
        referenced = set(re.findall(r"/output/([a-z0-9-]+\.(?:svg|gif|png))", self.readme))
        expected = {
            "hero.svg",
            "systems-reel.gif",
            "systems-reel-mobile.gif",
            "systems-reel-still.png",
            "systems-reel-mobile-still.png",
            "jump-projects.svg",
            "jump-experience.svg",
            "jump-activity.svg",
            "jump-contact.svg",
            "dossier-toggle.svg",
            "identity-console.svg",
            "proof-apps.svg",
            "proof-tests.svg",
            "proof-accuracy.svg",
            "proof-prototypes.svg",
            "nav-portfolio.svg",
            "nav-projects.svg",
            "nav-resume.svg",
            "nav-linkedin.svg",
            "nav-live.svg",
            "nav-source.svg",
            "nav-experiment.svg",
            "nav-email.svg",
            "nav-github.svg",
            "nav-devpost.svg",
            "nav-steam.svg",
            "signal-strip.svg",
            "section-projects.svg",
            "section-field.svg",
            "project-dossier-portfolio.svg",
            "project-dossier-helios.svg",
            "project-dossier-zenith.svg",
            "project-dossier-vision.svg",
            "project-dossier-talks.svg",
            "project-dossier-feelings.svg",
            "project-portfolio-v2.svg",
            "project-portfolio-mobile-v2.svg",
            "project-helios.svg",
            "project-zenith.svg",
            "project-vision.svg",
            "project-talks.svg",
            "section-arsenal.svg",
            "arsenal.svg",
            "skills-matrix.svg",
            "field-notes.svg",
            "section-record.svg",
            "stats.svg",
            "contribution-stream.svg",
            "section-operator.svg",
            "operator-gateway.svg",
            "achievement-rack.svg",
            "protocol-engineer.svg",
            "protocol-product.svg",
            "protocol-human.svg",
            "section-channel.svg",
            "finale.svg",
        }

        self.assertEqual(referenced, expected)

    def test_project_art_urls_are_cache_versioned(self):
        for filename in generate_readme.PROJECT_VISUALS.values():
            if filename == "project-portfolio-v2.svg":
                continue
            self.assertIn(f"output/{filename}?rev=raster-v1", self.readme)


if __name__ == "__main__":
    unittest.main()
