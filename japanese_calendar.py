# =========================================================
# JAPANESE CALENDAR UTILITIES
# Unified conversion between Japanese era years (Nengo) and
# the Gregorian calendar.
# =========================================================

import re
from typing import Optional, Tuple

# Base year for each era.  Gregorian = base + era_year.
ERA_BASE_YEARS = {
    "\u4ee4\u548c": 2018,   # Reiwa
    "\u5e73\u6210": 1988,   # Heisei
    "\u662d\u548c": 1925,   # Showa
    "\u5927\u6b63": 1911,   # Taisho
    "\u660e\u6cbb": 1867,   # Meiji
}

# Latin-letter shortcuts used in some documents.
ERA_LETTER_MAP = {
    "R": "\u4ee4\u548c",
    "H": "\u5e73\u6210",
    "S": "\u662d\u548c",
    "T": "\u5927\u6b63",
    "M": "\u660e\u6cbb",
}

_REIWA_YEAR_RE = re.compile(r"\u4ee4\u548c\s*(\d+)\u5e74")


def convert_era_year(era: str, year) -> int:
    """Convert a Japanese-era year to Gregorian.

    ``era`` is a kanji string such as ``"\u4ee4\u548c"`` or ``"\u5e73\u6210"``.

    Raises ``ValueError`` for an unknown era.
    """
    year = int(year)
    base = ERA_BASE_YEARS.get(era)
    if base is None:
        raise ValueError(f"Era japonesa desconhecida: {era}")
    return base + year


def extract_reiwa_year_regex(text: str) -> Optional[int]:
    """Extract the Gregorian year from a Reiwa-era string using a strict regex.

    Returns ``None`` when no match is found.
    """
    match = _REIWA_YEAR_RE.search(text)
    if match:
        return convert_era_year("\u4ee4\u548c", int(match.group(1)))
    return None


def convert_japanese_date(s) -> Optional[str]:
    """Convert a Japanese-era date string to ``YYYY-MM-DD``.

    Supports Reiwa, Heisei, Showa, Taisho, Meiji and plain
    ``\u5e74\u6708\u65e5`` formatted dates.  Returns ``None`` on failure.
    """
    try:
        if not s:
            return None

        s = str(s).strip()

        if re.match(r"\d{4}-\d{2}-\d{2}", s):
            return s

        def _era_convert(era_kanji, text):
            """Helper: extract numbers and convert for the given era."""
            reiwa_year = None
            if era_kanji == "\u4ee4\u548c":
                reiwa_year = extract_reiwa_year_regex(text)

            if reiwa_year:
                mes_match = re.search(r"(\d+)\u6708", text)
                dia_match = re.search(r"(\d+)\u65e5", text)
                mes = mes_match.group(1) if mes_match else "01"
                dia = dia_match.group(1) if dia_match else "01"
                return f"{reiwa_year}-{mes.zfill(2)}-{dia.zfill(2)}"

            n = re.findall(r"\d+", text)
            base = ERA_BASE_YEARS[era_kanji]
            if len(n) >= 3:
                ano = base + int(n[0])
                return f"{ano}-{int(n[1]):02d}-{int(n[2]):02d}"
            if len(n) == 1:
                ano = base + int(n[0])
                return f"{ano}-01-01"
            return None

        for kanji, letter in [
            ("\u4ee4\u548c", "R"),
            ("\u5e73\u6210", "H"),
            ("\u662d\u548c", "S"),
            ("\u5927\u6b63", "T"),
            ("\u660e\u6cbb", "M"),
        ]:
            if kanji in s or s.startswith(letter):
                result = _era_convert(kanji, s)
                if result:
                    return result

        if "\u5e74" in s and "\u6708" in s and "\u65e5" in s:
            n = re.findall(r"\d+", s)
            if len(n) >= 3:
                return f"{int(n[0]):04d}-{int(n[1]):02d}-{int(n[2]):02d}"

        return None
    except Exception:
        return None
