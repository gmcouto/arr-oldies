"""Unit tests for LanguageNormalizer audio language extraction, ISO-639 normalization, and matching."""

import pytest

from arr_oldies.inventory.languages import LanguageNormalizer


@pytest.fixture
def normalizer() -> LanguageNormalizer:
    return LanguageNormalizer()


def test_extract_languages_simple(normalizer: LanguageNormalizer):
    """Verify single language string extraction."""
    langs = normalizer.extract_languages("eng")
    assert langs == ["English"]


def test_extract_languages_compound_delimiters(normalizer: LanguageNormalizer):
    """Verify extraction across varied delimiters: '/', ',', '+', '|', ';', '\\'."""
    assert normalizer.extract_languages("eng/fre") == ["English", "French"]
    assert normalizer.extract_languages("Japanese, English") == ["Japanese", "English"]
    assert normalizer.extract_languages("deu+ita") == ["German", "Italian"]
    assert normalizer.extract_languages("[EN+DE]") == ["English", "German"]
    assert normalizer.extract_languages("rus|spa;por\\kor") == ["Russian", "Spanish", "Portuguese", "Korean"]


def test_extract_languages_none_or_empty(normalizer: LanguageNormalizer):
    """Verify None and blank strings return empty list."""
    assert normalizer.extract_languages(None) == []
    assert normalizer.extract_languages("") == []
    assert normalizer.extract_languages("   ") == []


def test_extract_languages_deduplication(normalizer: LanguageNormalizer):
    """Verify deduplication preserves encounter order."""
    assert normalizer.extract_languages("eng/English/en") == ["English"]


def test_extract_languages_unknown_fallback(normalizer: LanguageNormalizer):
    """Verify unmapped language tokens are preserved without crashing."""
    assert normalizer.extract_languages("klingon/eng") == ["klingon", "English"]


@pytest.mark.parametrize(
    "query,item_langs,expected",
    [
        ("ja", ["Japanese"], True),
        ("jpn", ["Japanese"], True),
        ("japanese", ["Japanese"], True),
        ("JAPANESE", ["Japanese"], True),
        ("jap", ["Japanese"], True),
        ("fre", ["English", "French"], True),
        ("fra", ["French"], True),
        ("fr", ["French"], True),
        ("de", ["English", "Japanese"], False),
        ("spa", ["English"], False),
        ("zh", ["Chinese"], True),
        ("mandarin", ["Chinese"], True),
        ("en", ["English"], True),
        ("en-us", ["English"], True),
        ("", ["English"], False),
        ("   ", ["English"], False),
    ],
)
def test_language_matching(normalizer: LanguageNormalizer, query: str, item_langs: list[str], expected: bool):
    """Verify bidirectional ISO code, synonym, and name matching."""
    assert normalizer.matches(item_langs, query) is expected
