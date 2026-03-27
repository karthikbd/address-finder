# address-finder

[![PyPI version](https://badge.fury.io/py/address-finder.svg)](https://pypi.org/project/address-finder/)
[![Python versions](https://img.shields.io/pypi/pyversions/address-finder)](https://pypi.org/project/address-finder/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/karthikbd/address-finder/badge)](https://securityscorecards.dev/viewer/?uri=github.com/karthikbd/address-finder)

A **fully offline, self-contained** Python address parser and expander powered by [libpostal](https://github.com/openvenues/libpostal).

- **Zero network calls** at import or runtime — all model data is bundled and cached locally
- **Global model** — parses addresses in 60+ languages and scripts
- **Offline-first** — works in air-gapped and firewalled environments after install
- **Windows & Linux** support with pre-compiled native binaries included
- **Lazy loading** — library initialises on first parse/expand call, not at import time

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
  - [parse\_address](#parse_addressaddress-languagenone-countrynone)
  - [expand\_address](#expand_addressaddress-languagesnone)
- [How It Works](#how-it-works)
- [Data Packages](#data-packages)
- [Supported Platforms](#supported-platforms)
- [Build from Source](#build-from-source)
- [Running Tests](#running-tests)
- [CI / CD](#ci--cd)
- [Security](#security)
- [License](#license)

---

## Installation

```bash
pip install address-finder
```

This installs the main package **and** automatically pulls in `address-finder-data`, which contains the compressed, quantized libpostal model weights split across 12 chunk packages.

> **First-run note:** On first import the model data is decompressed once to `~/.cache/address_finder/`. All subsequent imports are instant.

---

## Quick Start

```python
from address_finder import parse_address, expand_address

# Parse a US address into labelled components
result = parse_address("781 Franklin Ave Crown Heights Brooklyn NYC NY 11216 USA")
# [('house_number', '781'), ('road', 'franklin ave'), ('suburb', 'crown heights'),
#  ('city_district', 'brooklyn'), ('city', 'nyc'), ('state', 'ny'),
#  ('postcode', '11216'), ('country', 'usa')]

# Expand address abbreviations into canonical form
variants = expand_address("Quatre vingt douze R. de la Roquette")
# ['92 rue de la roquette']
```

---

## API Reference

### `parse_address(address, language=None, country=None)`

Parse a raw address string into labelled components.

**Parameters**

| Parameter  | Type           | Description |
|------------|----------------|-------------|
| `address`  | `str`          | Raw address string (any language/script) |
| `language` | `str \| None`  | ISO 639-1 language hint, e.g. `'en'`, `'fr'`, `'de'` (optional) |
| `country`  | `str \| None`  | ISO 3166-1 alpha-2 country hint, e.g. `'us'`, `'de'` (optional) |

**Returns:** `list[tuple[str, str]]` — list of `(label, value)` pairs.

**Common labels:** `house_number`, `road`, `suburb`, `city_district`, `city`,
`state_district`, `state`, `postcode`, `country`, `unit`, `level`, `entrance`,
`po_box`, `near`.

**Examples**

```python
from address_finder import parse_address

# Country hint improves accuracy
parse_address("10 Downing Street London SW1A 2AA", country="gb")
# [('house_number', '10'), ('road', 'downing street'),
#  ('city', 'london'), ('postcode', 'sw1a 2aa')]

# German address with language + country hints
parse_address("Unter den Linden 77, 10117 Berlin", language="de", country="de")
# [('road', 'unter den linden'), ('house_number', '77'),
#  ('postcode', '10117'), ('city', 'berlin')]

# Japanese address (no hints needed)
parse_address("東京都渋谷区神南1-19-11")
# [('state', '東京都'), ('city_district', '渋谷区'),
#  ('road', '神南'), ('house_number', '1-19-11')]
```

---

### `expand_address(address, languages=None)`

Normalize and expand an address string into canonical variant(s).

**Parameters**

| Parameter   | Type               | Description |
|-------------|--------------------|-------------|
| `address`   | `str`              | Raw address string |
| `languages` | `list[str] \| None`| ISO 639-1 language hints (optional) |

**Returns:** `list[str]` — deduplicated list of normalized address forms.

**Examples**

```python
from address_finder import expand_address

# Expand US abbreviations
expand_address("123 Main St Springfield IL")
# ['123 main street springfield illinois']

# French expansion with language hint
expand_address("Quatre vingt douze R. de la Roquette", languages=["fr"])
# ['92 rue de la roquette']

# Multiple normalized variants
expand_address("Friedrichstraße 176-179 Berlin")
# ['friedrichstrasse 176-179 berlin', 'friedrichstraße 176-179 berlin']
```

---

## How It Works

```
pip install address-finder
        │
        ├── address_finder/             ← Python package (this repo)
        │   ├── _libs/postal.dll        ← pre-compiled Windows native library
        │   ├── _libs/libpostal.so.1    ← pre-compiled Linux native library
        │   ├── parser.py               ← ctypes bindings for libpostal_parse_address
        │   ├── expander.py             ← ctypes bindings for libpostal_expand_address
        │   └── _init_data.py           ← decompresses model data to ~/.cache on first use
        │
        └── address-finder-data/        ← companion data package (auto-installed)
            ├── p00 … p11               ← 12 lzma-compressed model weight chunks
            └── assembled to ~/.cache/address_finder/ on first import
```

The native binaries (`postal.dll` / `libpostal.so.1`) are loaded at runtime via
`ctypes`. The model data (quantized int8 weights + trie structures) is stored as
12 lzma-compressed split chunks in `address-finder-data-p00` through
`address-finder-data-p11`. On the first import, chunks are assembled and
decompressed once into your local cache directory.

---

## Data Packages

Model data is distributed as a meta-package that pulls in 12 split data chunks:

| Package | PyPI | Description |
|---------|------|-------------|
| [`address-finder-data`](https://pypi.org/project/address-finder-data/) | [![data](https://img.shields.io/pypi/v/address-finder-data)](https://pypi.org/project/address-finder-data/) | Meta-package — installs all 12 chunks |
| `address-finder-data-p00` … `address-finder-data-p11` | `1.0.2` | Split lzma-compressed data chunks |

The meta-package is installed automatically. To install it explicitly:

```bash
pip install address-finder-data
```

---

## Supported Platforms

| Platform | Architecture | Status |
|----------|-------------|--------|
| Windows  | x86-64 (AMD64) | ✅ Supported — `postal.dll` bundled |
| Linux    | x86-64 (manylinux2014) | ✅ Supported — `libpostal.so.1` bundled |
| macOS    | — | ❌ Not supported (no pre-built binary) |

**Python versions:** 3.9 · 3.10 · 3.11 · 3.12

---

## Build from Source

### Linux

```bash
# 1. Compile libpostal and place the shared library
bash scripts/build_libpostal.sh

# 2. Build wheel
pip install build
python -m build --wheel

# 3. Install locally
pip install dist/address_finder-*.whl
```

### Windows

```powershell
# Automated build (uses WSL internally for libpostal compilation)
python scripts/full_build_windows.py
```

Step-by-step manual build: see [`scripts/build_windows.ps1`](scripts/build_windows.ps1).

### Building Data Packages

The 12 chunk data packages are built and uploaded separately:

```bash
cd address-finder-data-dist
python build_and_upload_chunks.py
```

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

The test suite covers:

- Package metadata (version format, `__all__` exports)
- Public callable surface (`parse_address`, `expand_address`)
- Real address parsing and expansion across multiple languages
- Language and country hint handling
- Unicode and multi-script inputs
- Empty and edge-case inputs

---

## CI / CD

| Workflow | Trigger | Description |
|----------|---------|-------------|
| [Build Wheels](.github/workflows/build_wheels.yml) | Push `v*.*.*` tag | Builds Windows + Linux wheels |
| [OpenSSF Scorecard](.github/workflows/scorecard.yml) | Weekly + push to `main` | Security posture scan |

Dependabot is configured to keep Actions dependencies up to date
(see [`.github/dependabot.yml`](.github/dependabot.yml)).

---

## Security

Please review [SECURITY.md](SECURITY.md) for vulnerability reporting guidelines.
Do not open public GitHub issues for security vulnerabilities — use
[GitHub Security Advisories](https://github.com/karthikbd/address-finder/security/advisories/new) instead.

---

## License

[MIT](LICENSE) © Karthikeyan Balasundaram

---

## Links

- **PyPI:** https://pypi.org/project/address-finder/
- **Data package:** https://pypi.org/project/address-finder-data/
- **Issues:** https://github.com/karthikbd/address-finder/issues
- **libpostal upstream:** https://github.com/openvenues/libpostal
