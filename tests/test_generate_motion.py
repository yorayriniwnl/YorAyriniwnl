import importlib.util
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_motion.py"
spec = importlib.util.spec_from_file_location("generate_motion", SCRIPT)
generate_motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_motion)


class GenerateMotionTests(unittest.TestCase):
    def test_kinetic_primer_is_compact_animated_gif(self):
        payload = generate_motion.build_kinetic_primer_gif()

        self.assertLess(len(payload), 500_000)
        with Image.open(BytesIO(payload)) as image:
            self.assertEqual(image.format, "GIF")
            self.assertEqual(image.size, (1200, 240))
            self.assertTrue(image.is_animated)
            self.assertEqual(image.n_frames, generate_motion.FRAME_COUNT)
            self.assertEqual(image.info.get("loop"), 0)

            image.seek(0)
            first = image.convert("RGB")
            image.seek(image.n_frames // 2)
            middle = image.convert("RGB")
            self.assertIsNotNone(ImageChops.difference(first, middle).getbbox())


if __name__ == "__main__":
    unittest.main()
