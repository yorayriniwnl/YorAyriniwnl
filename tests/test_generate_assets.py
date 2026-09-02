import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_assets.py"
spec = importlib.util.spec_from_file_location("generate_assets", SCRIPT)
generate_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_assets)


class GenerateAssetsTests(unittest.TestCase):
    def test_cinematic_hero_is_self_contained_valid_svg(self):
        svg = generate_assets.build_cinematic_hero_svg(generate_assets.CONFIG)

        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("data:image/jpeg;base64,", svg)
        self.assertIn("AYR // OPERATOR ONLINE", svg)
        self.assertIn("FULL-STACK DEVELOPER", svg)
        self.assertIn('values="1492;1516;1492"', svg)

    def test_navigation_and_canonical_project_card_render_valid_svg(self):
        nav = generate_assets.build_nav_button_svg(
            "RÉSUMÉ", "VIEW PUBLIC RECORD", "▤", generate_assets.CONFIG, 42
        )
        project = next(
            item for item in generate_assets.PROFILE["projects"] if item["id"] == "vision"
        )
        card = generate_assets.build_project_card_svg(
            generate_assets.canonical_project_card_spec(project),
            generate_assets.CONFIG,
        )

        self.assertTrue(ET.fromstring(nav).tag.endswith("svg"))
        self.assertTrue(ET.fromstring(card).tag.endswith("svg"))
        self.assertIn("AI VS. REAL IMAGE DETECTOR", card)
        self.assertIn("78.5% HELD-OUT TEST ACCURACY", card.upper())
        self.assertIn("LBP", card)
        self.assertIn("GLCM", card)
        self.assertIn("FORENSIC WORKBENCH", card)
        self.assertIn("data:image/jpeg;base64,", card)

    def test_flagship_cards_have_distinct_visual_worlds_and_motion_grammar(self):
        manifest = generate_assets.build_asset_manifest()
        expected = {
            "helios": ("INDUSTRIAL TELEMETRY", "#ff1f2d", "EVENT TOPOLOGY", "SYNTHETIC DEMO"),
            "zenith": ("DAYLIGHT SOLAR INTELLIGENCE", "#d30b24", "3D ROOF PLANNING", "IRR"),
            "vision": ("FORENSIC TEXTURE LAB", "#d30b24", "FEATURE VECTOR", "78.5%"),
            "talks": ("REALTIME COMMUNICATION", "#ff1f2d", "MESSAGE FLOW", "PRESENCE"),
        }
        old_world_colors = (
            "#f0a64a", "#0e8a78", "#169cab", "#5be8ff", "#a78bff",
            "#e84b4b", "#b92b2b", "#ff8a7f", "#671515",
        )

        for kind, markers in expected.items():
            card = manifest[f"project-{kind}.svg"]
            with self.subTest(project=kind):
                self.assertTrue(all(marker in card for marker in markers))
                self.assertIn(f'class="{kind}-motion"', card)
                self.assertIn("prefers-reduced-motion: reduce", card)
                self.assertIn(
                    generate_assets.asset_data_uri(
                        generate_assets.VISUAL_CONTRACT["project_art"][kind]
                    ).split(",", 1)[1],
                    card,
                )
                for old_color in old_world_colors:
                    self.assertNotIn(old_color, card)

        for filename, svg in manifest.items():
            with self.subTest(asset=filename, palette="legacy"):
                for old_color in old_world_colors:
                    self.assertNotIn(old_color, svg)

        self.assertNotEqual(
            manifest["project-helios.svg"].split("<image", 1)[0],
            manifest["project-talks.svg"].split("<image", 1)[0],
        )

    def test_manifest_contains_only_public_readme_assets(self):
        manifest = generate_assets.build_asset_manifest()
        expected = {
            "hero.svg",
            "identity-console.svg",
            "signal-strip.svg",
            "field-notes.svg",
            "skills-matrix.svg",
            "proof-apps.svg",
            "proof-tests.svg",
            "proof-accuracy.svg",
            "proof-prototypes.svg",
            "operator-gateway.svg",
            "achievement-rack.svg",
            "protocol-engineer.svg",
            "protocol-product.svg",
            "protocol-human.svg",
            "project-portfolio-v2.svg",
            "project-portfolio-mobile-v2.svg",
            "dossier-toggle.svg",
            "jump-projects.svg",
            "jump-experience.svg",
            "jump-activity.svg",
            "jump-contact.svg",
            "project-helios.svg",
            "project-zenith.svg",
            "project-vision.svg",
            "project-talks.svg",
            "project-dossier-portfolio.svg",
            "project-dossier-helios.svg",
            "project-dossier-zenith.svg",
            "project-dossier-vision.svg",
            "project-dossier-talks.svg",
            "project-dossier-feelings.svg",
            "arsenal.svg",
            "finale.svg",
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
            "section-projects.svg",
            "section-field.svg",
            "section-arsenal.svg",
            "section-record.svg",
            "section-operator.svg",
            "section-channel.svg",
        }

        self.assertEqual(set(manifest), expected)
        # The flagship cards now embed retina-density raster derivatives. The
        # standalone 4K masters stay outside the SVG payload, but the larger
        # display derivatives still need a realistic aggregate budget.
        self.assertLess(sum(len(svg.encode("utf-8")) for svg in manifest.values()), 4_600_000)
        self.assertNotIn("project-next.svg", manifest)
        self.assertNotIn("+18.4%", "".join(manifest.values()))

    def test_supporting_assets_receive_atlas_treatment_but_flagship_art_stays_locked(self):
        manifest = generate_assets.build_asset_manifest()

        treated = set(manifest) - generate_assets.ATLAS_TREATMENT_EXCLUDED
        self.assertEqual(len(treated), 43)
        for filename in treated:
            with self.subTest(asset=filename):
                svg = manifest[filename]
                self.assertIn('id="atlas-treatment"', svg)
                self.assertIn('data-visual-treatment="atlas-v4"', svg)
                self.assertIn('aria-hidden="true"', svg)
                self.assertIn("prefers-reduced-motion: reduce", svg)
                self.assertTrue(ET.fromstring(svg).tag.endswith("svg"))

        for filename in generate_assets.ATLAS_TREATMENT_EXCLUDED:
            with self.subTest(asset=filename):
                self.assertNotIn('data-visual-treatment="atlas-v1"', manifest[filename])

        self.assertIn(generate_assets.asset_data_uri(generate_assets.VISUAL_CONTRACT["optimized_hero"]).split(",", 1)[1], manifest["hero.svg"])

    def test_visual_content_panels_are_valid_and_data_complete(self):
        manifest = generate_assets.build_asset_manifest()
        profile = generate_assets.PROFILE

        for filename in (
            "identity-console.svg",
            "field-notes.svg",
            "skills-matrix.svg",
            "project-dossier-portfolio.svg",
            "project-dossier-feelings.svg",
        ):
            with self.subTest(asset=filename):
                root = ET.fromstring(manifest[filename])
                self.assertTrue(root.tag.endswith("svg"))
                self.assertIn("<title>", manifest[filename])

        for proof in profile["proof"]:
            card = manifest[f'proof-{proof["id"]}.svg']
            self.assertIn(proof["value"], card)
            self.assertIn(proof["label"], card)
            self.assertIn(proof["detail"].upper().split()[0], card)

        for project in profile["projects"]:
            dossier = manifest[f'project-dossier-{project["id"]}.svg']
            self.assertIn(project["name"].upper(), dossier)
            self.assertIn(project["status"].upper(), dossier)
            for proof in project["proof"]:
                self.assertIn(proof, dossier)

    def test_new_showcase_is_accessible_and_respects_reduced_motion(self):
        for mobile in (False, True):
            svg = generate_assets.build_featured_project_svg(generate_assets.CONFIG, mobile)
            root = ET.fromstring(svg)
            self.assertEqual(root.get("role"), "img")
            self.assertIn("prefers-reduced-motion:reduce", svg)
            self.assertIn("illustrative artwork", svg)
            self.assertNotIn("<script", svg)
            self.assertNotIn("<foreignObject", svg)
            for proof in generate_assets.PROFILE["projects"][0]["proof"]:
                self.assertIn(proof, svg)

        for index, label in enumerate(("PROJECTS", "EXPERIENCE", "ACTIVITY", "CONTACT")):
            svg = generate_assets.build_jump_button_svg(label, index)
            self.assertTrue(ET.fromstring(svg).tag.endswith("svg"))
            self.assertIn("prefers-reduced-motion:reduce", svg)

    def test_dense_copy_is_preceded_by_contextual_kinetic_glyphs(self):
        manifest = generate_assets.build_asset_manifest()

        for kind in ("gpu", "realtime", "vision", "telecom"):
            self.assertIn(f'data-kinetic-glyph="{kind}"', manifest["identity-console.svg"])

        for proof in generate_assets.PROFILE["proof"]:
            self.assertIn(
                f'data-kinetic-glyph="{proof["id"]}"',
                manifest[f'proof-{proof["id"]}.svg'],
            )

        dossier = manifest["project-dossier-portfolio.svg"]
        for kind in ("mission", "proof", "stack"):
            self.assertIn(f'data-kinetic-glyph="{kind}"', dossier)

        for kind in ("telecom", "education"):
            self.assertIn(f'data-kinetic-glyph="{kind}"', manifest["field-notes.svg"])

        for kind in ("product", "backend", "ml", "platform", "expanding"):
            self.assertIn(f'data-kinetic-glyph="{kind}"', manifest["skills-matrix.svg"])

    def test_operator_mode_assets_are_valid_and_complete(self):
        assets = {
            "gateway": generate_assets.build_operator_gateway_svg(generate_assets.CONFIG),
            "rack": generate_assets.build_achievement_rack_svg(generate_assets.CONFIG),
            "trace": generate_assets.build_protocol_engineer_svg(generate_assets.CONFIG),
            "forge": generate_assets.build_protocol_product_svg(generate_assets.CONFIG),
            "archive": generate_assets.build_protocol_human_svg(generate_assets.CONFIG),
        }

        for name, svg in assets.items():
            with self.subTest(asset=name):
                self.assertTrue(ET.fromstring(svg).tag.endswith("svg"))

        self.assertIn("INITIATE OPERATOR MODE", assets["gateway"])
        self.assertIn("ACHIEVEMENTS UNLOCKED", assets["rack"])
        self.assertIn("Architecture starts at the constraint", assets["trace"])
        self.assertIn("Make the difficult", assets["forge"])
        self.assertIn("GRIND. BUILD. REPEAT.", assets["archive"])


if __name__ == "__main__":
    unittest.main()
