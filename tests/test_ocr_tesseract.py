"""Tests for ocr_tesseract.py – pure helper functions.

Covers: convert_japanese_year, find_target_line, parse_japanese_date,
        validate_year, debug_log, upscale_image, extract_registration_roi
"""

import importlib
import sys
from unittest.mock import MagicMock

import numpy as np
import pytest


@pytest.fixture()
def tess(monkeypatch):
    """Import ocr_tesseract after mocking heavy deps (cv2, pytesseract)."""
    # Stub cv2 so the module loads even without OpenCV
    fake_cv2 = MagicMock()
    fake_cv2.COLOR_BGR2GRAY = 6
    fake_cv2.ADAPTIVE_THRESH_GAUSSIAN_C = 1
    fake_cv2.THRESH_BINARY = 0
    fake_cv2.INTER_CUBIC = 2

    def _resize(img, dsize, interpolation=None):
        return np.zeros((dsize[1], dsize[0]), dtype=np.uint8)

    fake_cv2.resize = _resize
    fake_cv2.GaussianBlur = lambda img, k, s: img
    fake_cv2.adaptiveThreshold = lambda *a, **kw: a[0]
    fake_cv2.cvtColor = lambda img, code: img
    fake_cv2.imread = MagicMock(return_value=None)
    fake_cv2.imwrite = MagicMock()

    fake_pytesseract = MagicMock()

    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract)

    sys.modules.pop("ocr_tesseract", None)

    import ocr_tesseract

    return ocr_tesseract


# ------------------------------------------------------------------
# convert_japanese_year
# ------------------------------------------------------------------

class TestConvertJapaneseYear:
    def test_reiwa(self, tess):
        assert tess.convert_japanese_year("令和", 5) == 2023

    def test_heisei(self, tess):
        assert tess.convert_japanese_year("平成", 30) == 2018

    def test_showa(self, tess):
        assert tess.convert_japanese_year("昭和", 64) == 1989

    def test_unknown_era(self, tess):
        with pytest.raises(ValueError, match="desconhecida"):
            tess.convert_japanese_year("???", 1)


# ------------------------------------------------------------------
# find_target_line
# ------------------------------------------------------------------

class TestFindTargetLine:
    def test_finds_label(self, tess):
        text = "foo\n初度登録年月 令和5年3月\nbar"
        assert "初度登録年月" in tess.find_target_line(text)

    def test_finds_alternate_label(self, tess):
        text = "foo\n初度検査年月 令和6年4月\nbar"
        assert "初度検査年月" in tess.find_target_line(text)

    def test_raises_when_not_found(self, tess):
        with pytest.raises(ValueError, match="não encontrada"):
            tess.find_target_line("no labels here\njust random text")

    def test_split_label_not_found(self, tess):
        text = "初度登録\n年月\n令和5年3月"
        with pytest.raises(ValueError, match="não encontrada"):
            tess.find_target_line(text)

    def test_finds_label_with_context(self, tess):
        text = "header\n記録年月日 令和5年3月\nfooter"
        result = tess.find_target_line(text)
        assert "記録年月日" in result


# ------------------------------------------------------------------
# parse_japanese_date
# ------------------------------------------------------------------

class TestParseJapaneseDate:
    def test_reiwa(self, tess):
        year, month = tess.parse_japanese_date("初度登録年月 令和5年3月")
        assert year == 2023
        assert month == 3

    def test_heisei(self, tess):
        year, month = tess.parse_japanese_date("初度検査年月 平成30年12月")
        assert year == 2018
        assert month == 12

    def test_showa(self, tess):
        year, month = tess.parse_japanese_date("記録年月日 昭和64年1月")
        assert year == 1989
        assert month == 1

    def test_no_date_raises(self, tess):
        with pytest.raises(ValueError, match="válida"):
            tess.parse_japanese_date("no date here")


# ------------------------------------------------------------------
# validate_year
# ------------------------------------------------------------------

class TestValidateYear:
    def test_valid_year(self, tess):
        tess.validate_year(2024)  # should not raise

    def test_min_boundary(self, tess):
        tess.validate_year(1990)  # should not raise

    def test_max_boundary(self, tess):
        tess.validate_year(2035)  # should not raise

    def test_below_min(self, tess):
        with pytest.raises(ValueError, match="inválido"):
            tess.validate_year(1989)

    def test_above_max(self, tess):
        with pytest.raises(ValueError, match="inválido"):
            tess.validate_year(2036)


# ------------------------------------------------------------------
# debug_log / save_debug_image
# ------------------------------------------------------------------

class TestDebugHelpers:
    def test_debug_log_runs(self, tess, capsys):
        tess.DEBUG_MODE = True
        tess.debug_log("hello")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_debug_log_silent_when_off(self, tess, capsys):
        tess.DEBUG_MODE = False
        tess.debug_log("hello")
        captured = capsys.readouterr()
        assert "hello" not in captured.out


# ------------------------------------------------------------------
# extract_registration_roi
# ------------------------------------------------------------------

class TestExtractRegistrationRoi:
    def test_roi_dimensions(self, tess):
        img = np.zeros((1000, 800, 3), dtype=np.uint8)
        roi = tess.extract_registration_roi(img)
        assert roi.shape[0] > 0
        assert roi.shape[1] > 0
        assert roi.shape[0] < img.shape[0]
        assert roi.shape[1] < img.shape[1]
