"""Tests for the public address_finder package surface."""
import address_finder
from address_finder import parse_address, expand_address


# ── package metadata ──────────────────────────────────────────────────────────

def test_version_exists():
    assert hasattr(address_finder, "__version__")


def test_version_is_string():
    assert isinstance(address_finder.__version__, str)


def test_version_format():
    """Version must look like X.Y.Z or X.Y.Z.postN."""
    parts = address_finder.__version__.split(".")
    assert len(parts) >= 3


def test_all_declared():
    assert hasattr(address_finder, "__all__")
    assert "parse_address" in address_finder.__all__
    assert "expand_address" in address_finder.__all__


# ── public callables ──────────────────────────────────────────────────────────

def test_parse_address_is_callable():
    assert callable(parse_address)


def test_expand_address_is_callable():
    assert callable(expand_address)


# ── cross-function consistency ────────────────────────────────────────────────

def test_parse_and_expand_same_address():
    """Both functions accept the same input without raising."""
    addr = "22 Rue de Rivoli Paris 75004 France"
    parse_result   = parse_address(addr)
    expand_result  = expand_address(addr)
    assert isinstance(parse_result, list)
    assert isinstance(expand_result, list)


def test_parse_result_non_empty_for_real_address():
    result = parse_address("123 Main Street Springfield IL 62701 USA")
    assert len(result) > 0


def test_expand_result_non_empty_for_real_address():
    result = expand_address("123 Main St Springfield IL")
    assert len(result) > 0


def test_parse_address_uses_module_attribute():
    """Calling via module attribute must produce the same result as direct import."""
    addr = "10 Downing Street London"
    assert address_finder.parse_address(addr) == parse_address(addr)


def test_expand_address_uses_module_attribute():
    addr = "123 Main St"
    assert address_finder.expand_address(addr) == expand_address(addr)
