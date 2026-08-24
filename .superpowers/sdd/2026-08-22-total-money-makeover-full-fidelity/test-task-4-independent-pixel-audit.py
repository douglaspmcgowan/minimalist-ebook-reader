import importlib.util
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


MODULE_PATH = Path(__file__).with_name("task-4-independent-pixel-audit.py")
SPEC = importlib.util.spec_from_file_location("pixel_audit", MODULE_PATH)
pixel_audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pixel_audit)
PDF_AUDIT_PATH = Path(__file__).with_name("task-4-independent-pdf-audit.py")
PDF_AUDIT_SPEC = importlib.util.spec_from_file_location("pdf_audit", PDF_AUDIT_PATH)
pdf_audit = importlib.util.module_from_spec(PDF_AUDIT_SPEC)
PDF_AUDIT_SPEC.loader.exec_module(pdf_audit)


def synthetic_page(seed: int) -> Image.Image:
    image = Image.new("RGB", (240, 312), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((18 + seed, 24, 220, 44), fill=(20, 30 + seed, 40))
    for row in range(8):
        top = 64 + row * 24
        draw.rectangle((24, top, 180 + ((row + seed) % 3) * 14, top + 5), fill=(30, 30, 30))
    draw.ellipse((45 + seed * 2, 245, 95 + seed * 2, 295), fill=(80, 120, 160))
    return image


class PixelAuditTests(unittest.TestCase):
    def test_pdf_audit_exact_visual_claim_requires_passing_all_page_pixel_evidence(self):
        aggregate = {
            "pagesCompared": 229,
            "pagesPassed": 229,
            "dimensionMatches": 229,
            "mappingTopChoiceMatches": 229,
            "uniqueDecodedAssets": 229,
        }
        passing = {
            "audit": "independent-poppler-pixel-comparison",
            "pass": True,
            "aggregate": aggregate,
        }
        self.assertTrue(pdf_audit.pixel_audit_claim(passing))
        self.assertFalse(pdf_audit.pixel_audit_claim({**passing, "aggregate": {**aggregate, "pagesPassed": 228}}))
        self.assertFalse(pdf_audit.pixel_audit_claim({**passing, "pass": False}))

    def test_similarity_tolerances_accept_compression_and_reject_blank_or_shifted_pages(self):
        reference = synthetic_page(1)
        compressed = pixel_audit.webp_round_trip(reference)
        correct = pixel_audit.page_similarity(reference, compressed)
        self.assertTrue(pixel_audit.similarity_passes(correct), correct)

        blank = pixel_audit.page_similarity(reference, Image.new("RGB", reference.size, "white"))
        self.assertFalse(pixel_audit.similarity_passes(blank), blank)

        shifted_array = np.full((312, 240, 3), 255, dtype=np.uint8)
        source_array = np.asarray(reference)
        shifted_array[12:, 10:] = source_array[:-12, :-10]
        shifted = pixel_audit.page_similarity(reference, Image.fromarray(shifted_array))
        self.assertFalse(pixel_audit.similarity_passes(shifted), shifted)

    def test_mapping_discriminator_rejects_wrong_and_duplicated_page_assignments(self):
        references = [pixel_audit.feature_vector(synthetic_page(seed)) for seed in range(4)]
        correct_assets = [pixel_audit.feature_vector(pixel_audit.webp_round_trip(synthetic_page(seed))) for seed in range(4)]
        correct = pixel_audit.mapping_discriminators(references, correct_assets)
        self.assertTrue(all(item["pass"] for item in correct), correct)

        wrong_assets = correct_assets[1:] + correct_assets[:1]
        wrong = pixel_audit.mapping_discriminators(references, wrong_assets)
        self.assertFalse(all(item["pass"] for item in wrong), wrong)

        duplicated_assets = list(correct_assets)
        duplicated_assets[2] = duplicated_assets[1]
        duplicated = pixel_audit.mapping_discriminators(references, duplicated_assets)
        self.assertFalse(all(item["pass"] for item in duplicated), duplicated)


if __name__ == "__main__":
    unittest.main()
