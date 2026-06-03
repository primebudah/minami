"""Tests for ocr_service.py – pure helper functions.

Covers: traduzir_veiculo, calcular_ano_reiwa, extrair_ano_reiwa_regex,
        extrair_placa, converter_data_japonesa
"""

import importlib
import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def ocr(monkeypatch):
    """Import ocr_service after mocking out OpenAI."""
    fake_openai = MagicMock()
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    # Provide a fake OPENAI_API_KEY so module-level init doesn't KeyError
    st = sys.modules["streamlit"]
    st.secrets["OPENAI_API_KEY"] = "fake-key-for-tests"

    # Remove cached module so re-import picks up mocks
    sys.modules.pop("ocr_service", None)

    import ocr_service  # noqa: E402

    return ocr_service


# ------------------------------------------------------------------
# traduzir_veiculo
# ------------------------------------------------------------------

class TestTraduzirVeiculo:
    def test_translates_known_manufacturer(self, ocr):
        assert ocr.traduzir_veiculo("トヨタ") == "Toyota"

    def test_translates_known_model(self, ocr):
        assert ocr.traduzir_veiculo("プリウス") == "Prius"

    def test_translates_combined(self, ocr):
        result = ocr.traduzir_veiculo("トヨタ プリウス")
        assert "Toyota" in result
        assert "Prius" in result

    def test_returns_original_when_no_match(self, ocr):
        assert ocr.traduzir_veiculo("FooBar") == "FooBar"

    def test_empty_string(self, ocr):
        assert ocr.traduzir_veiculo("") == ""

    def test_none_input(self, ocr):
        assert ocr.traduzir_veiculo(None) is None

    def test_multiple_replacements(self, ocr):
        result = ocr.traduzir_veiculo("日産 スカイライン")
        assert "Nissan" in result
        assert "Skyline" in result


# ------------------------------------------------------------------
# calcular_ano_reiwa
# ------------------------------------------------------------------

class TestCalcularAnoReiwa:
    def test_reiwa_1(self, ocr):
        assert ocr.calcular_ano_reiwa(1) == 2019

    def test_reiwa_5(self, ocr):
        assert ocr.calcular_ano_reiwa(5) == 2023

    def test_reiwa_8(self, ocr):
        assert ocr.calcular_ano_reiwa(8) == 2026

    def test_reiwa_string_number(self, ocr):
        assert ocr.calcular_ano_reiwa("7") == 2025


# ------------------------------------------------------------------
# extrair_ano_reiwa_regex
# ------------------------------------------------------------------

class TestExtrairAnoReiwaRegex:
    def test_standard(self, ocr):
        assert ocr.extrair_ano_reiwa_regex("令和8年5月10日") == 2026

    def test_with_spaces(self, ocr):
        assert ocr.extrair_ano_reiwa_regex("令和 5年") == 2023

    def test_no_reiwa(self, ocr):
        assert ocr.extrair_ano_reiwa_regex("平成30年") is None

    def test_empty(self, ocr):
        assert ocr.extrair_ano_reiwa_regex("") is None


# ------------------------------------------------------------------
# extrair_placa
# ------------------------------------------------------------------

class TestExtrairPlaca:
    def test_empty_input(self, ocr):
        assert ocr.extrair_placa("") == ""

    def test_none_input(self, ocr):
        assert ocr.extrair_placa(None) == ""

    def test_alphanumeric_plate(self, ocr):
        result = ocr.extrair_placa("ABC-1234")
        assert len(result) >= 4

    def test_short_alpha_plate(self, ocr):
        result = ocr.extrair_placa("AB1234")
        assert len(result) >= 4


# ------------------------------------------------------------------
# converter_data_japonesa
# ------------------------------------------------------------------

class TestConverterDataJaponesa:
    def test_already_gregorian(self, ocr):
        assert ocr.converter_data_japonesa("2024-05-10") == "2024-05-10"

    def test_reiwa_full(self, ocr):
        assert ocr.converter_data_japonesa("令和8年5月10日") == "2026-05-10"

    def test_reiwa_year_month_only(self, ocr):
        result = ocr.converter_data_japonesa("令和5年3月")
        assert result is not None
        assert result.startswith("2023-03")

    def test_heisei_full(self, ocr):
        assert ocr.converter_data_japonesa("平成30年12月25日") == "2018-12-25"

    def test_heisei_year_only(self, ocr):
        result = ocr.converter_data_japonesa("平成30")
        assert result is not None
        assert result.startswith("2018")

    def test_showa(self, ocr):
        assert ocr.converter_data_japonesa("昭和64年1月7日") == "1989-01-07"

    def test_taisho(self, ocr):
        assert ocr.converter_data_japonesa("大正15年12月25日") == "1926-12-25"

    def test_meiji(self, ocr):
        assert ocr.converter_data_japonesa("明治45年7月30日") == "1912-07-30"

    def test_empty(self, ocr):
        assert ocr.converter_data_japonesa("") is None

    def test_none(self, ocr):
        assert ocr.converter_data_japonesa(None) is None

    def test_garbage(self, ocr):
        assert ocr.converter_data_japonesa("garbage") is None

    def test_standard_japanese_format(self, ocr):
        assert ocr.converter_data_japonesa("2024年3月15日") == "2024-03-15"

    def test_reiwa_with_r_prefix(self, ocr):
        result = ocr.converter_data_japonesa("R8年5月10日")
        assert result is not None
        assert result.startswith("2026")

    def test_heisei_with_h_prefix(self, ocr):
        result = ocr.converter_data_japonesa("H30年12月25日")
        assert result is not None
        assert result.startswith("2018")

    def test_showa_with_s_prefix(self, ocr):
        result = ocr.converter_data_japonesa("S64年1月7日")
        assert result is not None
        assert result.startswith("1989")
