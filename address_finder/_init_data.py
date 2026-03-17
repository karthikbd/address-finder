"""
Provide address-finder model data on first import (~1.9 GB, one-time setup).

Priority order:
  1. Already assembled/downloaded → instant return.
  2. address-finder-data package installed → decompress from chunks (offline).
  3. Fall back to downloading from GitHub releases (~1.9 GB).

Cache location: ~/.cache/address_finder/v1.0.0/
To clear:       address_finder._init_data.clear_cache()
"""
import tarfile
import pathlib
import logging
import urllib.request

log = logging.getLogger(__name__)

_DATA_VERSION = "v1.0.0"
_CACHE_DIR    = pathlib.Path.home() / ".cache" / "address_finder"
_DATA_DIR     = _CACHE_DIR / _DATA_VERSION  # contains address_parser/, language_classifier/, …
_STAMP        = _DATA_DIR / ".downloaded"

_BASE_URL = "https://github.com/openvenues/libpostal/releases/download/v1.0.0"
_ARCHIVES = [
    ("libpostal_data.tar.gz",      "base data (address expansions, transliteration, numex) ~30 MB"),
    ("language_classifier.tar.gz", "language classifier model ~70 MB"),
    ("parser.tar.gz",              "address parser model ~700 MB download"),
]


def _download(url: str, dest: pathlib.Path, desc: str) -> None:
    """Download url to dest, printing a simple progress indicator."""
    print(f"  Downloading {desc}", flush=True)

    def _hook(count: int, block: int, total: int) -> None:
        if total > 0:
            pct = min(100, count * block * 100 // total)
            done_mb = count * block / 1_000_000
            tot_mb  = total / 1_000_000
            print(f"\r    {pct:3d}%  {done_mb:6.0f} / {tot_mb:.0f} MB", end="", flush=True)

    urllib.request.urlretrieve(url, str(dest), _hook)
    print()  # newline after progress bar


def _try_companion_package() -> bool:
    """
    If address-finder-data is installed, use it to assemble data.
    Returns True if successful, False if not available.
    """
    try:
        import address_finder_data  # type: ignore[import]
    except ImportError:
        return False

    try:
        address_finder_data.assemble(cache_dir=_DATA_DIR)
        return True
    except Exception as exc:
        log.warning("address_finder: companion package assembly failed: %s", exc)
        return False


def ensure_data() -> str:
    """
    Return path to the address-finder data directory, setting it up on first call.

    1. If cache stamp exists → instant return (already ready).
    2. If address-finder-data package is installed → assemble from chunks.
    3. Otherwise → download ~1.9 GB from GitHub releases.
    """
    if _STAMP.exists():
        log.debug("address_finder: using cached data at %s", _DATA_DIR)
        return str(_DATA_DIR)

    # Try offline companion package first
    assembled_stamp = _DATA_DIR / ".assembled"
    if assembled_stamp.exists():
        # Companion package already ran assemble() — just write our stamp
        _STAMP.touch()
        return str(_DATA_DIR)

    if _try_companion_package():
        # assemble() succeeded — it writes .assembled; write our stamp too
        _STAMP.touch()
        return str(_DATA_DIR)

    # Fall back: download from GitHub
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _DATA_DIR / "_tmp"
    tmp.mkdir(exist_ok=True)

    print("address_finder: First-run data download (~1.9\u202fGB uncompressed, one-time setup).",
          flush=True)
    print(f"  Destination: {_DATA_DIR}", flush=True)

    for filename, desc in _ARCHIVES:
        dest = tmp / filename
        _download(f"{_BASE_URL}/{filename}", dest, desc)
        print(f"  Extracting {filename} …", flush=True)
        with tarfile.open(str(dest), "r:gz") as tf:
            tf.extractall(str(_DATA_DIR))
        dest.unlink()

    tmp.rmdir()
    _STAMP.touch()
    print("address_finder: Data ready.", flush=True)
    return str(_DATA_DIR)


def clear_cache() -> None:
    """Delete cached data (forces re-download on next import)."""
    import shutil
    if _CACHE_DIR.exists():
        shutil.rmtree(_CACHE_DIR)
        print(f"Cache cleared: {_CACHE_DIR}")
