"""
Skip all tests when libpostal shared library has not been built yet.
Build with:   python scripts\\full_build_windows.py --skip-data

Model data is downloaded automatically on first test run (~1.9 GB, one-time).
"""
import pathlib
import pytest

_LIB_DIR = pathlib.Path(__file__).parent / "address_finder" / "_libs"

_LIBS_PRESENT = (
    any(_LIB_DIR.glob("postal.dll"))
    or any(_LIB_DIR.glob("libpostal.so*"))
    or any(_LIB_DIR.glob("libpostal.*.dylib"))
)


def pytest_runtest_setup(item):
    """Skip every test when the compiled library is missing."""
    if not _LIBS_PRESENT:
        pytest.skip(
            "postal.dll / libpostal.so not found in address_finder/_libs/. "
            "Run: python scripts\\full_build_windows.py"
        )
