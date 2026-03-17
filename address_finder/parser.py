"""parse_address() — wraps the native parse function via ctypes."""
import ctypes
from typing import List, Tuple
from address_finder._lib_loader import get_lib, _ParseOptions


def parse_address(
    address: str,
    language: str | None = None,
    country: str  | None = None,
) -> List[Tuple[str, str]]:
    """
    Parse a raw address string into labeled components.

    Returns a list of (label, value) tuples, e.g.:
        [('house_number', '781'), ('road', 'franklin ave'), ...]

    Parameters
    ----------
    address  : raw address string (any language/script)
    language : ISO 639-1 hint, e.g. 'en', 'fr', 'de' (optional)
    country  : ISO 3166-1 alpha-2 hint, e.g. 'us', 'de'  (optional)
    """
    lib = get_lib()
    opts = lib.libpostal_get_address_parser_default_options()
    if language:
        opts.language = language.encode()
    if country:
        opts.country = country.encode()

    # parse_address returns address_parser_response_t*
    # struct { size_t num_components; char** components; char** labels; }
    response = lib.libpostal_parse_address(address.encode("utf-8"), opts)
    if not response:
        return []

    resp = response.contents
    n = resp.num_components
    pairs = [
        (
            resp.labels[i].decode("utf-8")     if resp.labels[i]     else "",
            resp.components[i].decode("utf-8") if resp.components[i] else "",
        )
        for i in range(n)
    ]

    lib.libpostal_address_parser_response_destroy(response)
    return pairs
