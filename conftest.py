"""
Skip all tests when libpostal has not been built yet.
Build it with:
  1. PowerShell (with WSL available):  .\\scripts\\build_windows.ps1
  2. Then:                             python scripts\\build_package.py
"""
import pathlib
import pytest

_DATA_BUNDLE = pathlib.Path(__file__).parent / "address_finder" / "_data.tar.zst"
_LIB_DIR     = pathlib.Path(__file__).parent / "address_finder" / "_libs"

_LIBS_PRESENT = any(_LIB_DIR.glob("postal.dll")) or any(_LIB_DIR.glob("libpostal.so*"))
_DATA_PRESENT = _DATA_BUNDLE.exists()

_SKIP_REASON = []
if not _DATA_PRESENT:
    _SKIP_REASON.append("_data.tar.zst missing (run scripts/build_package.py)")
if not _LIBS_PRESENT:
    _SKIP_REASON.append("postal.dll/_libs missing (run scripts/build_windows.ps1)")


def pytest_runtest_setup(item):
    """Skip every test when prereqs are missing."""
    if _SKIP_REASON:
        pytest.skip("libpostal not built: " + "; ".join(_SKIP_REASON))
