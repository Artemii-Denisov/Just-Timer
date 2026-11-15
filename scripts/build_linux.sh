#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Building Just Timer for Linux via PyInstaller..."
python3 -m PyInstaller --clean --onefile --noconsole \
    --name "Just-Timer-Linux" \
    --add-data="assets:assets" \
    --paths="src" \
    run.py

echo "Build complete: dist/Just-Timer-Linux"
