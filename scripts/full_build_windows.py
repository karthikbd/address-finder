"""
Full build orchestrator for address-finder — Windows edition.
Runs entirely from Python on Windows; uses WSL only for DLL compilation.

Steps:
  1. Build postal.dll via MinGW cross-compile in WSL (with native exports flag)
  2. Build wheel (python -m build)

Model data (~1 GB) is downloaded automatically at runtime on first import
from GitHub releases v1.0.0 — no bundling required.

Usage:
    python scripts/full_build_windows.py
    python scripts/full_build_windows.py --skip-dll   # if postal.dll already present
"""
import argparse
import pathlib
import subprocess
import sys

ROOT    = pathlib.Path(__file__).parent.parent.resolve()
LIB_DIR = ROOT / "address_finder" / "_libs"

WSL_DLL_DIR = "/root/libpostal_linux"  # persists across WSL sessions

# ─────────────────────────────────────────────────────────────────────────────

def wsl(cmd: str, check=True) -> str:
    """Run a bash command in WSL Ubuntu-20.04 as root, return stdout."""
    result = subprocess.run(
        ["wsl", "-d", "Ubuntu-20.04", "-u", "root", "bash", "-c", cmd],
        capture_output=True, text=True,
    )
    if check and result.returncode != 0:
        print(f"WSL ERROR:\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def banner(text: str):
    print(f"\n{'='*60}\n  {text}\n{'='*60}")


# ─────────────────────────────────────────────────────────────────────────────

def build_dll():
    banner("Step 1: Build postal.dll via MinGW in WSL")

    wsl_libs = wsl(f"wslpath -u '{str(LIB_DIR).replace(chr(92), '/')}'")

    script = f"""#!/bin/bash
set -euo pipefail
CLONE_DIR="{WSL_DLL_DIR}"
WSL_LIBS="{wsl_libs}"
mkdir -p "$WSL_LIBS"

if [ ! -d "$CLONE_DIR" ]; then
    echo "[DLL] Cloning libpostal..."
    git clone --depth 1 https://github.com/openvenues/libpostal "$CLONE_DIR"
fi

cd "$CLONE_DIR"

# Clean any previous build
make distclean 2>/dev/null || true

echo "[DLL] bootstrap..."
./bootstrap.sh 2>&1 | tail -3

echo "[DLL] configure for MinGW with LIBPOSTAL_EXPORTS..."
./configure --host=x86_64-w64-mingw32 \\
            --enable-shared --disable-static \\
            --datadir=/root/postal_raw \\
            --disable-data-download \\
            CFLAGS='-O2 -DLIBPOSTAL_EXPORTS' 2>&1 | tail -5

echo "[DLL] building..."
make -j4 -C src libpostal.la 2>&1 | tail -10

DLL=$(find "$CLONE_DIR/src/.libs" -name 'libpostal-1.dll' -o -name 'postal.dll' 2>/dev/null | head -1)
if [ -z "$DLL" ]; then
    echo "ERROR: no .dll produced"; exit 1
fi
cp "$DLL" "$WSL_LIBS/postal.dll"
echo "OK: copied $(basename $DLL) -> $WSL_LIBS/postal.dll"
"""

    tmp = pathlib.Path(r"C:\Users\karthikeyan1\AppData\Local\Temp\af_dll.sh")
    tmp.write_text(script, encoding="utf-8", newline="\n")
    wsl("cp /mnt/c/Users/karthikeyan1/AppData/Local/Temp/af_dll.sh /root/af_dll.sh && chmod +x /root/af_dll.sh")

    print("Running MinGW DLL build (~10-15 min)...\n")
    subprocess.run(
        ["wsl", "-d", "Ubuntu-20.04", "-u", "root", "bash", "/root/af_dll.sh"],
        text=True, capture_output=False,
    )

    dll = LIB_DIR / "postal.dll"
    if dll.exists():
        print(f"\npostal.dll  {dll.stat().st_size / 1e6:.1f} MB  OK")
    else:
        print("\nWARNING: postal.dll not found — something went wrong")


def build_wheel():
    banner("Step 2: Build wheel")
    r = subprocess.run(
        [sys.executable, "-m", "build", "--wheel"],
        check=False, cwd=str(ROOT),
    )
    if r.returncode != 0:
        print("\nTip: pip install build")
        sys.exit(1)
    wheels = sorted((ROOT / "dist").glob("address_finder*.whl"))
    if wheels:
        w = wheels[-1]
        print(f"\nBuilt: {w.name}  ({w.stat().st_size / 1e6:.1f} MB)")
        print(f"Install: pip install \"{w}\"")


# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Build address-finder wheel on Windows")
    ap.add_argument("--skip-dll", action="store_true",
                    help="Skip DLL build (use existing postal.dll)")
    args = ap.parse_args()

    banner("address-finder — Windows Build")
    print("  Model data is downloaded at runtime (~1 GB, once only).")
    print("  No quantization or bundling needed.\n")

    if not args.skip_dll:
        build_dll()
    else:
        dll = LIB_DIR / "postal.dll"
        size = f"{dll.stat().st_size / 1e6:.1f} MB" if dll.exists() else "MISSING"
        print(f"[1] Skipping DLL build  (postal.dll: {size})")

    build_wheel()

    banner("DONE")
    print("\nRun tests:  pytest tests/ -v")
    print("Upload:     twine upload dist/address_finder*.whl")


if __name__ == "__main__":
    main()
