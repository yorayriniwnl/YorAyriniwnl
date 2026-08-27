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

    def test_primary_narrative_is_semantic_and_proof_first(self):
        headings = [
            "## Selected systems",
            "## Field notes",
            "## Technical range",
            "## Public record",
            "## Operator mode",
            "## Open channel",
        ]
        positions = [self.readme.index(heading) for heading in headings]

        self.assertEqual(positions, sorted(positions))
        self.assertLess(self.readme.index("## Selected systems"), self.readme.index("## Operator mode"))
        for project_id in generate_readme.SELECTED_PROJECT_IDS:
            project = next(item for item in self.profile["projects"] if item["id"] == project_id)
            self.assertIn(project["name"], self.readme)
            for proof in project["proof"]:
                self.assertIn(proof, self.readme)

    def test_layout_is_mobile_safe_and_images_are_accessible(self):
        image_tags = re.findall(r"<img\b[^>]*?/>", self.readme)
        widths = re.findall(r'width="([^"]+)"', self.readme)

        self.assertGreaterEqual(len(image_tags), 20)
        self.assertTrue(all(re.search(r'alt="[^"]+"', tag) for tag in image_tags))
        self.assertTrue(all(width in {"100%", "350"} for width in widths))
        self.assertNotIn('width="24%"', self.readme)
        self.assertNotIn('width="49%"', self.readme)
        for filename in generate_readme.PROJECT_VISUALS.values():
            self.assertIn(f'output/{filename}" width="100%"', self.readme)

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
        referenced = set(re.findall(r"/output/([a-z0-9-]+\.svg)", self.readme))
        expected = {
            "hero.svg",
            "nav-portfolio.svg",
            "nav-projects.svg",
            "nav-resume.svg",
            "nav-linkedin.svg",
            "signal-strip.svg",
            "section-projects.svg",
            "project-portfolio.svg",
            "project-helios.svg",
            "project-zenith.svg",
            "project-vision.svg",
            "project-talks.svg",
            "section-arsenal.svg",
            "arsenal.svg",
            "section-record.svg",
            "stats.svg",
            "operator-gateway.svg",
            "achievement-rack.svg",
            "protocol-engineer.svg",
            "protocol-product.svg",
            "protocol-human.svg",
            "finale.svg",
        }

        self.assertEqual(referenced, expected)


if __name__ == "__main__":
    unittest.main()
