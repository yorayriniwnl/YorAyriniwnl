import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "optimize_assets.py"
spec = importlib.util.spec_from_file_location("optimize_assets", SCRIPT)
optimize_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(optimize_assets)


class OptimizeAssetsTests(unittest.TestCase):
    def test_optimized_assets_are_valid_and_preserve_approved_hero(self):
        optimize_assets.validate_optimized_assets()

        hero, expected_sha = optimize_assets.approved_hero_contract()
        self.assertEqual(optimize_assets.sha256(hero), expected_sha)

    def test_optimized_payload_stays_under_two_megabytes(self):
        total = sum(
            (optimize_assets.ASSET_DIR / recipe.output).stat().st_size
            for recipe in optimize_assets.RECIPES
        )

        self.assertLess(total, 2_000_000)


if __name__ == "__main__":
    unittest.main()
