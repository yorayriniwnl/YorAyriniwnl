import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowTests(unittest.TestCase):
    def test_asset_workflow_validates_before_publishing(self):
        workflow = (WORKFLOWS / "build-assets.yml").read_text(encoding="utf-8")

        self.assertIn("pull_request:", workflow)
        self.assertIn("actions/setup-python@v5", workflow)
        self.assertIn("python scripts/profile_data.py", workflow)
        self.assertIn("python scripts/optimize_assets.py", workflow)
        self.assertIn("python main/scripts/generate_motion.py", workflow)
        self.assertIn("cp main/generated/systems-reel*.gif output/", workflow)
        self.assertIn("cp main/generated/systems-reel*-still.png output/", workflow)
        self.assertIn("git diff --exit-code -- assets", workflow)
        self.assertIn("python scripts/generate_readme.py --check", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertLess(workflow.index("Verify README"), workflow.index("Checkout output"))
        self.assertNotIn("schedule:", workflow)

    def test_output_sync_preserves_independent_dynamic_assets(self):
        workflow = (WORKFLOWS / "build-assets.yml").read_text(encoding="utf-8")

        for filename in (
            "stats.svg",
            "stats-mobile.svg",
            "contribution-stream.svg",
            "contribution-stream-mobile.svg",
        ):
            self.assertIn(f"! -name '{filename}'", workflow)
        self.assertNotIn("github-contribution-grid-snake", workflow)

    def test_stats_workflow_tracks_its_canonical_dependencies(self):
        workflow = (WORKFLOWS / "build-stats.yml").read_text(encoding="utf-8")

        self.assertIn('"data/profile.json"', workflow)
        self.assertIn('"scripts/profile_data.py"', workflow)
        self.assertIn("actions/setup-python@v5", workflow)
        self.assertIn("python main/scripts/generate_stats.py", workflow)

    def test_contribution_workflow_generates_owned_stream(self):
        workflow = (WORKFLOWS / "contribution-stream.yml").read_text(encoding="utf-8")

        self.assertIn("python main/scripts/generate_contributions.py", workflow)
        self.assertIn("contribution-stream*.svg", workflow)
        self.assertNotIn("Platane/snk", workflow)


if __name__ == "__main__":
    unittest.main()
