import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from tools.pdf_to_ebook.extract import extract_pdf


class ExtractionTests(unittest.TestCase):
    def test_bounded_extraction_skips_full_document_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp, "three-pages.pdf")
            writer = PdfWriter()
            for _ in range(3):
                writer.add_blank_page(width=612, height=792)
            with source.open("wb") as handle:
                writer.write(handle)

            preflight, records = extract_pdf(source, page_numbers=[2], include_preflight=False)

            self.assertEqual([2], preflight["requested_pages"])
            self.assertEqual([], records)


if __name__ == "__main__":
    unittest.main()
