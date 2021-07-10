"""Charmap Test Case

This module contains the test case for the Charmap Test. It prints the first
999 characters of the unicode character set with a unicode ttf font, and
verifies the result against a known good result.

This test will complain that some of the values in this font file are out of
the range of the C 'short' data type (2 bytes, 0 - 65535):
  fpdf/ttfonts.py:671: UserWarning: cmap value too big/small:
and this seems to be okay.
"""
from pathlib import Path
from unittest.mock import Mock

import pytest

import fpdf
from fpdf.ttfonts import TTFontFile
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize(
    "font_filename",
    ["DejaVuSans.ttf", "DroidSansFallback.ttf", "Roboto-Regular.ttf", "cmss12.ttf"],
)
def test_first_999_chars(font_filename, tmp_path):
    font_path = HERE / ".." / ".." / "fonts" / font_filename
    font_name = font_path.stem

    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font(font_name, fname=font_path, uni=True)
    pdf.set_font(font_name, size=10)

    ttf = TTFontFile()
    # Mock the function calls to record their output
    # Note: pylint does not like some of this
    ttf.getCMAP4 = Mock(side_effect=ttf.getCMAP4)
    ttf.getCMAP12 = Mock(side_effect=ttf.getCMAP12)

    ttf.getMetrics(font_path)

    characters = {}  # Map of ascii/unicode hex values to glyphs
    if ttf.getCMAP4.called:
        # pylint: disable=unsubscriptable-object
        characters = ttf.getCMAP4.call_args[0][2]
    if ttf.getCMAP12.called:
        # pylint: disable=unsubscriptable-object
        characters = ttf.getCMAP12.call_args[0][2]

    # Create a PDF with the first 999 charters defined in the font:
    for counter, character in enumerate(characters, 0):
        pdf.write(8, f"{counter:03}) {character:03x} - {character:c}")
        pdf.ln()
        if counter >= 999:
            break

    for pkl_path in HERE.glob("*.pkl"):
        pkl_path.unlink()

    assert_pdf_equal(pdf, HERE / f"charmap_first_999_chars-{font_name}.pdf", tmp_path)
    assert ttf.getCMAP4.called or ttf.getCMAP12.called
    if ttf.getCMAP4.called:
        assert (
            not ttf.getCMAP12.called
        ), "getCMAP12 should never be called at the same time as getCMAP4"
    if ttf.getCMAP12.called:
        assert (
            not ttf.getCMAP4.called
        ), "getCMAP4 should never be called at the same time as getCMAP12"
