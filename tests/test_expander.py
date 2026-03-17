"""Unit tests for expand_address."""
import pytest
from address_finder import expand_address


# ── basic happy-path ────────────────────────────────────────────────────────

def test_french_expansion():
    result = expand_address("Quatre vingt douze R. de la Roquette")
    assert any("92" in r for r in result)


def test_abbreviation_expansion():
    result = expand_address("123 Main St")
    assert any("street" in r for r in result)


def test_returns_list():
    result = expand_address("1 Av. des Champs-Elysées Paris")
    assert isinstance(result, list)
    assert len(result) >= 1


# ── return-type invariants ────────────────────────────────────────────────────

def test_all_expansions_are_strings():
    result = expand_address("123 Main St Springfield")
    assert all(isinstance(r, str) for r in result)


def test_expansions_are_lowercase():
    """The normaliser always lowercases output."""
    result = expand_address("123 Main Street")
    for r in result:
        assert r == r.lower()


def test_no_duplicates():
    result = expand_address("123 Main St")
    assert len(result) == len(set(result))


# ── edge cases ────────────────────────────────────────────────────────────────

def test_empty_string_returns_empty_list():
    result = expand_address("")
    assert result == []


def test_whitespace_only():
    result = expand_address("   ")
    assert isinstance(result, list)


def test_already_expanded_address():
    """A fully written-out address must still return at least one expansion."""
    result = expand_address("123 Main Street Springfield Illinois")
    assert isinstance(result, list)
    assert len(result) >= 1
    assert any("main street" in r for r in result)


def test_boulevard_abbreviation():
    result = expand_address("15 Blvd Haussmann Paris")
    assert any("boulevard" in r for r in result)


def test_avenue_abbreviation():
    result = expand_address("350 5th Ave New York")
    assert any("avenue" in r for r in result)


# ── optional languages hint ───────────────────────────────────────────────────

def test_with_languages_hint():
    """languages kwarg must not raise and must return valid expansions."""
    result = expand_address("10 Rue de la Paix Paris", languages=["fr"])
    assert isinstance(result, list)
    assert len(result) >= 1


def test_with_english_language_hint():
    result = expand_address("100 Main St", languages=["en"])
    assert any("street" in r for r in result)


# ── unicode / international ────────────────────────────────────────────────────

def test_unicode_input_does_not_raise():
    result = expand_address("Bahnhofstraße 1 Zürich")
    assert isinstance(result, list)
