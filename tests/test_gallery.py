import datetime as dt
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth

from scripts import gallery

ROOT = Path(__file__).parents[1]


class GalleryTests(unittest.TestCase):
    def test_capture_provenance_matches_reviewed_files(self):
        data = gallery.load_gallery()
        manifest = json.loads((ROOT / "assets/gallery/manifest.json").read_text())
        self.assertEqual({item["project"] for item in manifest}, set(data["featured"]))
        for item in manifest:
            for name, digest in (("source", "source_sha256"), ("optimized", "optimized_sha256")):
                path = ROOT / "assets/gallery" / item[name]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item[digest])
            self.assertEqual(item["source_url"], data["projects"][item["project"]]["media_url"])
            self.assertIn("no synthetic UI", item["processing"])
            self.assertLess(item["optimized_bytes"], 150_000)

    def test_shared_palette_has_readable_body_contrast(self):
        def luminance(hex_color):
            values = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
            channels = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in values]
            return sum(a*b for a, b in zip(channels, (.2126, .7152, .0722)))
        for foreground in (gallery.PAPER, gallery.MUTED, gallery.SIGNAL):
            for background in (gallery.VOID, gallery.PANEL, "#210c12"):
                self.assertGreaterEqual((luminance(foreground)+.05)/(luminance(background)+.05), 4.5)

    def test_controls_have_large_effective_targets(self):
        for toggle in (False, True):
            svg = gallery.button("UNDER THE HOOD" if toggle else "RÉSUMÉ", "file", toggle)
            root = ET.fromstring(svg)
            rendered_width = 180 if toggle else 140
            self.assertGreaterEqual(float(root.get("height"))*rendered_width/float(root.get("width")), 44)

    def test_all_new_sans_serif_labels_fit_horizontally(self):
        profile = json.loads((ROOT / "data/profile.json").read_text(encoding="utf-8"))
        assets = gallery.build_gallery_manifest(profile)
        days = [{"date": dt.date(2026, 8, 31) - dt.timedelta(days=i), "count": i % 7} for i in range(365)]
        for mobile in (False, True):
            assets[gallery.asset_name("record", mobile)] = gallery.render_public_record(
                {"public_repos": 25, "stars": 2, "followers": 0}, "31 Aug 2026 / 06:00 UTC", mobile)
            assets[gallery.asset_name("contributions", mobile)] = gallery.render_contributions(
                days, "31 Aug 2026 / 06:00 UTC", mobile)
        for name, svg in assets.items():
            root = ET.fromstring(svg)
            width = float(root.get("width"))
            for node in root.findall(".//{http://www.w3.org/2000/svg}text"):
                if node.get("class") != "sans":
                    continue
                font = "Helvetica-Bold" if int(node.get("font-weight", "400")) >= 600 else "Helvetica"
                text_width = stringWidth(node.text or "", font, float(node.get("font-size")))
                start = float(node.get("x"))
                if node.get("text-anchor") == "end":
                    start -= text_width
                with self.subTest(asset=name, label=node.text):
                    self.assertGreaterEqual(start, 8)
                    self.assertLessEqual(start + text_width, width - 8)

    def test_copy_wrapping_keeps_every_word(self):
        value = "A carefully explained system with meaningful evidence and a long identifier: authentication_configuration."
        lines = gallery.wrap(value, 528, 38)
        self.assertEqual("".join("".join(lines).split()), "".join(value.split()))
        self.assertGreater(len(lines), 1)

    def test_markup_in_copy_is_escaped(self):
        svg = gallery.shell(600, 150, "A & B", "<script>unsafe</script>", gallery.text(30, 70, '<img src="x">'))
        ET.fromstring(svg)
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;img", svg)

    def test_snapshots_have_dates_and_no_audience_fabrication(self):
        for mobile in (False, True):
            svg = gallery.render_public_record({"public_repos":25, "stars":2, "followers":0}, "31 Aug 2026 / 06:00 UTC", mobile)
            root = ET.fromstring(svg)
            text = " ".join(root.itertext())
            self.assertIn("31 Aug 2026", text)
            self.assertIn("Snapshot, not a live audience count.", " ".join(text.split()))
            self.assertNotIn("PROFILE VIEWS", text)
            self.assertIn(">0</text>", svg)

    def test_design_samples_are_never_labeled_live_metrics(self):
        svg = gallery.render_public_record({"_sample":True}, "design preview")
        self.assertIn("DESIGN SAMPLE / NOT LIVE", svg)
        self.assertNotIn(">0</text>", svg)

    def test_contribution_window_and_totals_are_exact(self):
        start = dt.date(2026, 1, 1)
        days = [{"date": start + dt.timedelta(days=i), "count": i % 4, "level": i % 4} for i in range(365)]
        for mobile in (False, True):
            svg = gallery.render_contributions(days, "31 Aug 2026", mobile)
            root = ET.fromstring(svg)
            text = " ".join(root.itertext())
            self.assertIn(str(sum(item["count"] for item in days)), text)
            self.assertIn("365 days", text)
            self.assertIn("13 weeks", text)
            self.assertNotIn("AUTO-REFRESH", text)
        with self.assertRaises(ValueError):
            gallery.render_contributions([], "31 Aug 2026")

    def test_review_scope_distinguishes_demos_from_source_studies(self):
        data = gallery.load_gallery()
        self.assertFalse(data["projects"]["helios"]["show_site"])
        self.assertFalse(data["projects"]["talks"]["show_site"])
        self.assertFalse(data["projects"]["feelings"]["show_site"])
        self.assertIn("not inference", data["projects"]["vision"]["evidence_note"])
        self.assertIn("not guarantees", data["projects"]["zenith"]["evidence_note"])


if __name__ == "__main__":
    unittest.main()
