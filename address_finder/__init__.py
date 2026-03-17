"""
address_finder — offline address parsing and expansion.
Data is decompressed once to ~/.cache/address_finder/ on first import.
The library is initialised lazily on first call to parse/expand.
"""
__version__ = "1.0.1"

_DATADIR = None
_LIB     = None


def _ensure_loaded():
    """Initialise the native library on first use (lazy, thread-safe enough for typical use)."""
    global _DATADIR, _LIB
    if _LIB is not None:
        return
    from address_finder._init_data import ensure_data
    from address_finder._lib_loader import _init_lib
    _DATADIR = ensure_data()
    _LIB     = _init_lib(_DATADIR)


def parse_address(address: str, language: str | None = None, country: str | None = None):
    """Parse an address string into labelled (label, value) components."""
    _ensure_loaded()
    from address_finder.parser import parse_address as _parse
    return _parse(address, language=language, country=country)


def expand_address(address: str, languages: list | None = None) -> list:
    """Expand address abbreviations/variants into canonical forms."""
    _ensure_loaded()
    from address_finder.expander import expand_address as _expand
    return _expand(address, languages=languages)


__all__ = ["parse_address", "expand_address"]
