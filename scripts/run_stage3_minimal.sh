#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python}"

rm -rf output/stage3_minimal
"$PYTHON" -m src.main --vfs examples/vfs/minimal --script scripts/stage3_minimal.sh
