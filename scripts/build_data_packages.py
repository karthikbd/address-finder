#!/usr/bin/env python3
"""
Build address-finder-data chunk packages from address-finder model files.

Usage (from Windows, calls WSL python3):
  wsl -d Ubuntu-20.04 -u root python3 /mnt/c/Users/karthikeyan1/PNC/package_build/scripts/build_data_packages.py

The script:
  1. Reads address-finder data files from DATA_SRC
  2. Compresses each with lzma (stdlib, no extra deps)
  3. Splits into CHUNK_SIZE byte chunks
  4. Creates one Python package dir per chunk
  5. Creates meta-package address-finder-data that depends on all chunks
  6. Builds all wheels via `python3 -m build`

Output directory: OUT_BASE (under package_build)
"""

import hashlib
import json
import lzma
import shutil
import textwrap
from pathlib import Path
from typing import Dict, List

# ── Configuration ────────────────────────────────────────────────────────────

DATA_SRC = Path("/root/postal_raw/libpostal")

# Output goes to /mnt/c/... (Windows filesystem via WSL)
SCRIPT_DIR = Path(__file__).parent
OUT_BASE = SCRIPT_DIR.parent / "address-finder-data-dist"

CHUNK_SIZE = 90 * 1024 * 1024  # 90 MB per chunk (leaves headroom for PyPI 100 MB limit)
VERSION = "1.0.0"

# Data files to package: (relative_src_path, canonical_name_for_reassembly)
DATA_FILES = [
    # Largest first so chunk numbering starts with CRF
    ("address_parser/address_parser_crf.dat",             "address_parser_crf.dat"),
    ("address_parser/address_parser_postal_codes.dat",    "address_parser_postal_codes.dat"),
    ("address_parser/address_parser_phrases.dat",         "address_parser_phrases.dat"),
    ("address_parser/address_parser_vocab.trie",          "address_parser_vocab.trie"),
    ("language_classifier/language_classifier.dat",       "language_classifier.dat"),
    ("transliteration/transliteration.dat",               "transliteration.dat"),
    ("address_expansions/address_dictionary.dat",         "address_dictionary.dat"),
    ("numex/numex.dat",                                   "numex.dat"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def compress_file(src: Path) -> bytes:
    """Read and lzma-compress a file, return compressed bytes."""
    print(f"  Compressing {src.name} ({src.stat().st_size // 1024 // 1024} MB)...", flush=True)
    data = src.read_bytes()
    compressed = lzma.compress(data, format=lzma.FORMAT_XZ, preset=1)
    ratio = len(compressed) * 100 // len(data)
    print(f"    → {len(compressed) // 1024 // 1024} MB ({ratio}%)", flush=True)
    return compressed


def split_chunks(data: bytes, chunk_size: int):
    """Yield (index, chunk_bytes) for each chunk."""
    total = len(data)
    idx = 0
    offset = 0
    while offset < total:
        yield idx, data[offset : offset + chunk_size]
        offset += chunk_size
        idx += 1


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── Package creators ──────────────────────────────────────────────────────────

def _pkg_name(chunk_idx: int) -> str:
    return f"address-finder-data-p{chunk_idx:02d}"


def _module_name(chunk_idx: int) -> str:
    return f"address_finder_data_p{chunk_idx:02d}"


def create_chunk_package(
    out_base: Path,
    chunk_idx: int,
    canonical_name: str,    # original filename
    file_chunk_index: int,  # which piece of this file (0,1,2,...)
    total_file_chunks: int, # how many pieces this file is split into
    chunk_bytes: bytes,
    chunk_sha256: str,
    file_compressed_size: int,
    file_original_size: int,
) -> dict:
    """Create package directory for one chunk and return metadata."""
    pkg_name = _pkg_name(chunk_idx)
    mod_name = _module_name(chunk_idx)
    pkg_dir = out_base / pkg_name
    mod_dir = pkg_dir / mod_name
    data_dir = mod_dir / "data"

    pkg_dir.mkdir(parents=True, exist_ok=True)
    mod_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    # Write the binary chunk
    chunk_file = data_dir / "chunk.bin"
    chunk_file.write_bytes(chunk_bytes)

    # Metadata for this chunk
    meta = {
        "canonical_name": canonical_name,
        "file_chunk_index": file_chunk_index,
        "total_file_chunks": total_file_chunks,
        "chunk_sha256": chunk_sha256,
        "file_compressed_size": file_compressed_size,
        "file_original_size": file_original_size,
        "chunk_size": len(chunk_bytes),
    }

    # __init__.py — tiny
    (mod_dir / "__init__.py").write_text(textwrap.dedent(f"""\
        import importlib.resources as _ir
        from pathlib import Path as _P

        # Chunk metadata
        CANONICAL_NAME = {canonical_name!r}
        FILE_CHUNK_INDEX = {file_chunk_index}
        TOTAL_FILE_CHUNKS = {total_file_chunks}
        CHUNK_SHA256 = {chunk_sha256!r}
        FILE_ORIGINAL_SIZE = {file_original_size}

        def chunk_path() -> _P:
            \"\"\"Return path to the raw compressed chunk file.\"\"\"\
            try:
                ref = _ir.files(__name__) / "data" / "chunk.bin"
                return _P(str(ref))
            except AttributeError:
                import pkg_resources
                return _P(pkg_resources.resource_filename(__name__, "data/chunk.bin"))
    """))

    # pyproject.toml
    (pkg_dir / "pyproject.toml").write_text(textwrap.dedent(f"""\
        [build-system]
        requires = ["setuptools>=61"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{pkg_name}"
        version = "{VERSION}"
        authors = [{{name = "Karthikeyan Balasundaram"}}]
        description = "address-finder data chunk p{chunk_idx:02d} — contains {canonical_name} part {file_chunk_index+1}/{total_file_chunks}"
        readme = "README.md"
        license = {{text = "MIT"}}
        requires-python = ">=3.8"
        keywords = ["address-finder", "address parser", "offline", "libpostal", "data"]
        classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Topic :: Scientific/Engineering :: GIS",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
        ]

        [project.urls]
        Homepage = "https://github.com/karthikbd/address-finder"
        Repository = "https://github.com/karthikbd/address-finder"

        [tool.setuptools.packages.find]
        where = ["."]

        [tool.setuptools.package-data]
        "{mod_name}" = ["data/chunk.bin"]
    """))

    # README
    (pkg_dir / "README.md").write_text(textwrap.dedent(f"""\
        # {pkg_name}

        Compressed data chunk for [address-finder](https://pypi.org/project/address-finder/).

        - File: `{canonical_name}`
        - Part {file_chunk_index + 1} of {total_file_chunks}
        - Compressed size: {len(chunk_bytes) // 1024 // 1024} MB

        **Do not install this package directly.** Install `address-finder-data` instead,
        which will pull in all required chunks automatically.
    """))

    print(f"  Created {pkg_name}: {len(chunk_bytes)//1024//1024} MB chunk "
          f"({canonical_name} part {file_chunk_index+1}/{total_file_chunks})")
    return meta


def create_meta_package(out_base: Path, manifest: List[Dict]):
    """Create the address-finder-data meta-package with assembler code."""
    pkg_dir = out_base / "address-finder-data"
    mod_dir = pkg_dir / "address_finder_data"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    mod_dir.mkdir(exist_ok=True)

    # Build dependency list
    all_chunk_pkgs = [f'address-finder-data-p{m["global_chunk_idx"]:02d}=={VERSION}' for m in manifest]
    dep_list = "\n".join(f'    "{p}",' for p in all_chunk_pkgs)

    # Build file→chunks mapping for assembler
    file_chunks: dict[str, list] = {}
    for m in manifest:
        fn = m["canonical_name"]
        if fn not in file_chunks:
            file_chunks[fn] = []
        file_chunks[fn].append(m["global_chunk_idx"])

    manifest_json = json.dumps(
        {
            "version": VERSION,
            "files": {
                fn: {
                    "original_size": next(
                        x["file_original_size"] for x in manifest if x["canonical_name"] == fn
                    ),
                    "chunk_packages": [_module_name(ci) for ci in idxs],
                }
                for fn, idxs in file_chunks.items()
            },
        },
        indent=2,
    )

    # address_finder_data/__init__.py — assembler
    (mod_dir / "__init__.py").write_text(textwrap.dedent(f"""\
        \"\"\"
        address-finder-data: companion data package for address-finder.

        On first import, call assemble() to decompress all data files into the
        cache directory and make them available to address-finder.
        \"\"\"
        from __future__ import annotations

        import importlib
        import json
        import lzma
        import os
        from pathlib import Path
        from typing import Optional

        __version__ = "{VERSION}"

        # Where address-finder looks for data
        DEFAULT_CACHE = Path.home() / ".cache" / "address_finder" / "v{VERSION}"

        # File destination sub-paths (relative to cache root)
        DEST_PATHS = {{
            "address_parser_crf.dat":          "address_parser/address_parser_crf.dat",
            "address_parser_postal_codes.dat":  "address_parser/address_parser_postal_codes.dat",
            "address_parser_phrases.dat":       "address_parser/address_parser_phrases.dat",
            "address_parser_vocab.trie":        "address_parser/address_parser_vocab.trie",
            "language_classifier.dat":          "language_classifier/language_classifier.dat",
            "transliteration.dat":              "transliteration/transliteration.dat",
            "address_dictionary.dat":           "address_expansions/address_dictionary.dat",
            "numex.dat":                        "numex/numex.dat",
        }}

        MANIFEST: dict = json.loads({manifest_json!r})


        def assemble(cache_dir: Path | None = None, force: bool = False) -> Path:
            \"\"\"
            Decompress and assemble all data files into *cache_dir*.

            Args:
                cache_dir: Target directory (default: ~/.cache/address_finder/v1.0.0).
                force: Re-assemble even if stamp file already exists.

            Returns:
                Path to the assembled data root.
            \"\"\"
            cache_dir = Path(cache_dir or DEFAULT_CACHE)
            stamp = cache_dir / ".assembled"

            if stamp.exists() and not force:
                return cache_dir

            print("address-finder-data: assembling data files…")
            cache_dir.mkdir(parents=True, exist_ok=True)

            for canonical_name, info in MANIFEST["files"].items():
                dest_rel = DEST_PATHS[canonical_name]
                dest = cache_dir / dest_rel
                dest.parent.mkdir(parents=True, exist_ok=True)

                if dest.exists() and not force:
                    print(f"  {{canonical_name}} already present, skipping")
                    continue

                print(f"  Assembling {{canonical_name}}…", end=" ", flush=True)

                # Collect compressed bytes from all chunk packages
                compressed_parts: list[bytes] = []
                for mod_name in info["chunk_packages"]:
                    mod = importlib.import_module(mod_name)
                    chunk_path = mod.chunk_path()
                    compressed_parts.append(chunk_path.read_bytes())

                compressed = b"".join(compressed_parts)
                print(f"decompressing {{len(compressed)//1024//1024}} MB…", end=" ", flush=True)
                data = lzma.decompress(compressed, format=lzma.FORMAT_XZ)
                dest.write_bytes(data)
                print(f"done ({{len(data)//1024//1024}} MB)")

            stamp.write_text("assembled")
            print(f"address-finder-data: all files ready at {{cache_dir}}")
            return cache_dir


        def is_assembled(cache_dir: Path | None = None) -> bool:
            \"\"\"Return True if data has already been assembled.\"\"\"\
            cache_dir = Path(cache_dir or DEFAULT_CACHE)
            return (cache_dir / ".assembled").exists()
    """))

    # pyproject.toml for meta-package
    (pkg_dir / "pyproject.toml").write_text(textwrap.dedent(f"""\
        [build-system]
        requires = ["setuptools>=61"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "address-finder-data"
        version = "{VERSION}"
        authors = [{{name = "Karthikeyan Balasundaram"}}]
        description = "Companion data package for address-finder (model files)"
        readme = "README.md"
        license = {{text = "MIT"}}
        requires-python = ">=3.8"
        keywords = ["address-finder", "address parser", "offline", "libpostal", "data"]
        classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Topic :: Scientific/Engineering :: GIS",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
        ]
        dependencies = [
        {dep_list}
        ]

        [project.urls]
        Homepage = "https://github.com/karthikbd/address-finder"
        Repository = "https://github.com/karthikbd/address-finder"
        "Bug Tracker" = "https://github.com/karthikbd/address-finder/issues"
        Documentation = "https://github.com/karthikbd/address-finder#readme"

        [tool.setuptools.packages.find]
        where = ["."]
    """))

    # README
    total_chunks = len(manifest)
    (pkg_dir / "README.md").write_text(textwrap.dedent(f"""\
        # address-finder-data

        Companion data package (~1.9 GB of model files) for
        [address-finder](https://pypi.org/project/address-finder/).

        ## Install

        ```
        pip install address-finder address-finder-data
        ```

        ## Usage

        On first use after installation, call `assemble()` to decompress the
        data into your local cache:

        ```python
        import address_finder_data
        address_finder_data.assemble()   # one-time decompression ~1.9 GB

        import address_finder
        address_finder.expand_address("123 main st")
        ```

        Or simply import `address_finder` — it will auto-detect that
        `address-finder-data` is installed and assemble the files on first use.

        ## Details

        - Contains {total_chunks} compressed data chunk packages
        - Total compressed size: ~824 MB across all chunks
        - Decompressed size: ~1.9 GB (stored in `~/.cache/address_finder/v{VERSION}/`)
        - No internet access needed after install
        - Data format: lzma/xz (Python stdlib, no extra dependencies)
    """))

    print(f"  Created address-finder-data meta-package "
          f"({total_chunks} chunk dependencies)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if OUT_BASE.exists():
        print(f"Removing existing output dir: {OUT_BASE}")
        shutil.rmtree(OUT_BASE)
    OUT_BASE.mkdir(parents=True)

    manifest: List[Dict] = []
    global_chunk_idx = 0

    for rel_src, canonical_name in DATA_FILES:
        src = DATA_SRC / rel_src
        if not src.exists():
            print(f"WARNING: {src} not found, skipping")
            continue

        original_size = src.stat().st_size
        print(f"\n=== {canonical_name} ({original_size // 1024 // 1024} MB) ===")

        compressed = compress_file(src)
        comp_size = len(compressed)
        chunks = list(split_chunks(compressed, CHUNK_SIZE))
        n_chunks = len(chunks)
        print(f"  Split into {n_chunks} chunk(s) of ≤{CHUNK_SIZE // 1024 // 1024} MB")

        for file_chunk_idx, chunk_bytes in chunks:
            sha = sha256_hex(chunk_bytes)
            meta = create_chunk_package(
                out_base=OUT_BASE,
                chunk_idx=global_chunk_idx,
                canonical_name=canonical_name,
                file_chunk_index=file_chunk_idx,
                total_file_chunks=n_chunks,
                chunk_bytes=chunk_bytes,
                chunk_sha256=sha,
                file_compressed_size=comp_size,
                file_original_size=original_size,
            )
            meta["global_chunk_idx"] = global_chunk_idx
            manifest.append(meta)
            global_chunk_idx += 1

    print(f"\n=== Creating meta-package ({global_chunk_idx} total chunks) ===")
    create_meta_package(OUT_BASE, manifest)

    # Save manifest JSON for reference
    manifest_path = OUT_BASE / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest saved to {manifest_path}")
    print(f"\nTotal packages: {global_chunk_idx} chunk packages + 1 meta-package")
    print(f"Output: {OUT_BASE}")
    print("\nNext step: build wheels")
    print("  cd <OUT_BASE>")
    print("  for d in address-finder-data-p*; do (cd $d && python3 -m build --wheel); done")
    print("  cd address-finder-data && python3 -m build --wheel")


if __name__ == "__main__":
    main()
