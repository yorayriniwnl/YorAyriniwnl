import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
DATA_PATH = ROOT / "data" / "profile.json"


class ProfileDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    def test_validator_accepts_canonical_data(self):
        from scripts.profile_data import validate_profile

        validate_profile(self.profile)

    def test_public_contact_uses_professional_email_and_no_phone(self):
        serialized = json.dumps(self.profile, ensure_ascii=False)

        self.assertEqual(self.profile["contact"]["email"], "ayushroy.dev@gmail.com")
        self.assertNotIn("yorayriniwnl@gmail.com", serialized)
        self.assertNotIn("89189", serialized)

    def test_applied_ml_claim_matches_resume_evidence(self):
        vision = next(project for project in self.profile["projects"] if project["id"] == "vision")
        evidence = " ".join([vision["summary"], *vision["proof"], *vision["stack"]]).lower()

        for term in ("lbp", "glcm", "svm", "78%", "sub-two-second"):
            self.assertIn(term, evidence)
        self.assertNotIn("cnn", evidence)
        self.assertNotIn("deep learning", evidence)

    def test_approved_hero_binary_is_unchanged(self):
        contract = self.profile["visual_contract"]
        digest = hashlib.sha256((ROOT / contract["approved_hero"]).read_bytes()).hexdigest()

        self.assertEqual(digest, contract["approved_hero_sha256"])

    def test_optimized_visual_contract_is_complete(self):
        contract = self.profile["visual_contract"]
        derivatives = [contract["optimized_hero"], *contract["project_art"].values()]

        self.assertEqual(set(contract["project_art"]), {"helios", "zenith", "vision", "talks"})
        for relative_path in derivatives:
            with self.subTest(asset=relative_path):
                path = ROOT / relative_path
                self.assertTrue(path.is_file())
                self.assertEqual(path.suffix, ".jpg")


if __name__ == "__main__":
    unittest.main()
