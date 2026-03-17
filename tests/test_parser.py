"""Unit tests for parse_address."""
import pytest
from address_finder import parse_address


# ── basic happy-path ────────────────────────────────────────────────────────

def test_us_address():
    result = dict(parse_address("781 Franklin Ave Brooklyn NYC NY 11216 USA"))
    assert result.get("house_number") == "781"
    assert "franklin ave" in result.get("road", "")
    assert result.get("country") == "usa"


def test_german_address():
    result = dict(parse_address("Platz der Republik 1, 11011 Berlin"))
    assert result.get("house_number") == "1"
    assert result.get("city") == "berlin"


def test_empty_input():
    assert parse_address("") == []


def test_returns_list_of_tuples():
    result = parse_address("10 Downing Street London")
    assert isinstance(result, list)
    assert all(isinstance(t, tuple) and len(t) == 2 for t in result)


# ── tuple order: (label, value) ──────────────────────────────────────────────

def test_tuple_order_is_label_then_value():
    """parse_address returns (label, value) tuples — convertible via dict()."""
    result = parse_address("221B Baker Street London")
    labels = [label for label, _ in result]
    assert "road" in labels or "house_number" in labels


def test_dict_conversion_gives_label_keys():
    """dict(parse_address(...)) must map label -> value."""
    d = dict(parse_address("1600 Pennsylvania Avenue NW Washington DC"))
    # 'house_number' is a label — it must be a key, not a value
    assert "house_number" in d
    assert d["house_number"] == "1600"


# ── field extraction ─────────────────────────────────────────────────────────

def test_uk_address_postcode():
    result = dict(parse_address("10 Downing Street, London, SW1A 2AA, UK"))
    assert result.get("postcode") == "sw1a 2aa"


def test_french_address():
    result = dict(parse_address("55 Rue du Faubourg Saint-Honoré 75008 Paris France"))
    assert result.get("house_number") == "55"
    assert result.get("city") == "paris"
    assert result.get("postcode") == "75008"


def test_us_address_with_state_and_zip():
    result = dict(parse_address("350 Fifth Avenue New York NY 10118"))
    assert result.get("house_number") == "350"
    assert result.get("postcode") == "10118"


# ── optional hints ───────────────────────────────────────────────────────────

def test_with_language_hint():
    """language hint must not raise and must still return valid results."""
    result = parse_address("10 Downing Street London", language="en")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_with_country_hint():
    """country hint must not raise and must still return valid results."""
    result = parse_address("10 Downing Street London", country="gb")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_with_both_hints():
    result = parse_address("1 Infinite Loop Cupertino CA", language="en", country="us")
    d = dict(result)
    assert d.get("house_number") == "1"


# ── value types ───────────────────────────────────────────────────────────────

def test_labels_and_values_are_strings():
    result = parse_address("123 Main Street Springfield IL 62701")
    for label, value in result:
        assert isinstance(label, str) and label != ""
        assert isinstance(value, str)


def test_no_duplicate_labels_for_simple_address():
    """A clean single-address string should not produce repeated labels."""
    result = parse_address("42 Wallaby Way Sydney NSW 2000")
    labels = [label for label, _ in result]
    assert len(labels) == len(set(labels))


# ── edge cases ────────────────────────────────────────────────────────────────

def test_whitespace_only_input():
    result = parse_address("   ")
    assert isinstance(result, list)


def test_unicode_address():
    """Non-ASCII input must not raise."""
    result = parse_address("東京都新宿区西新宿2-8-1")
    assert isinstance(result, list)


def test_address_number_only_road():
    result = parse_address("742 Evergreen Terrace Springfield")
    d = dict(result)
    assert d.get("house_number") == "742"
