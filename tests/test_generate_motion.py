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
    def test_responsive_reels_are_compact_and_genuinely_animated(self):
        for mobile, size in ((False, (900, 320)), (True, (600, 650))):
            with self.subTest(mobile=mobile):
                payload = generate_motion.build_systems_reel_gif(mobile)
                self.assertLess(len(payload), 500_000)
                with Image.open(BytesIO(payload)) as image:
                    self.assertEqual(image.format, "GIF")
                    self.assertEqual(image.size, size)
                    self.assertTrue(image.is_animated)
                    self.assertEqual(image.n_frames, generate_motion.FRAME_COUNT)
                    self.assertEqual(image.info.get("loop"), 0)
                    self.assertEqual(image.info.get("duration"), generate_motion.FRAME_DURATION)
                    first = image.convert("RGB")
                    image.seek(image.n_frames // 2)
                    middle = image.convert("RGB")
                    self.assertIsNotNone(ImageChops.difference(first, middle).getbbox())

    def test_posters_are_first_frames_and_motion_is_periodic(self):
        for mobile in (False, True):
            first = generate_motion.build_frame(0, mobile)
            cycle = generate_motion.build_frame(generate_motion.FRAME_COUNT, mobile)
            self.assertIsNone(ImageChops.difference(first, cycle).getbbox())
            poster = generate_motion.build_poster(mobile)
            buffer = BytesIO()
            poster.save(buffer, format="PNG", optimize=True)
            self.assertLess(len(buffer.getvalue()), 50_000)
            with Image.open(BytesIO(generate_motion.build_systems_reel_gif(mobile))) as gif:
                self.assertIsNone(ImageChops.difference(poster.convert("RGB"), gif.convert("RGB")).getbbox())


if __name__ == "__main__":
    unittest.main()
