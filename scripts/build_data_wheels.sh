#!/bin/bash
# Build all address-finder-data wheels (chunk packages + meta-package)
# Run from WSL: bash /mnt/c/Users/karthikeyan1/PNC/package_build/address-finder/scripts/build_data_wheels.sh

set -e

DIST_BASE="/mnt/c/Users/karthikeyan1/PNC/package_build/address-finder/address-finder-data-dist"
WHEELS_OUT="$DIST_BASE/wheels"

mkdir -p "$WHEELS_OUT"

# Install build if needed
python3 -m pip install build --quiet

echo "=== Building chunk package wheels ==="
for pkg_dir in "$DIST_BASE"/address-finder-data-p*/; do
    pkg_name=$(basename "$pkg_dir")
    echo "  Building $pkg_name..."
    cd "$pkg_dir"
    python3 -m build --wheel --outdir "$WHEELS_OUT" --no-isolation > /dev/null 2>&1
    echo "    Done"
done

echo ""
echo "=== Building meta-package wheel ==="
cd "$DIST_BASE/address-finder-data"
python3 -m build --wheel --outdir "$WHEELS_OUT" --no-isolation > /dev/null 2>&1
echo "    Done"

echo ""
echo "=== Wheel inventory ==="
ls -lh "$WHEELS_OUT"/*.whl | awk '{print $5, $9}'
echo ""
echo "Total wheels: $(ls "$WHEELS_OUT"/*.whl | wc -l)"
echo "Total size: $(du -sh "$WHEELS_OUT"/*.whl | tail -1 | cut -f1) (last file) — combined: $(du -sh "$WHEELS_OUT" | cut -f1)"
