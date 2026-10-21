#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python}"

rm -rf output/stage3_nested
"$PYTHON" -m src.main --vfs examples/vfs/nested --script scripts/stage3_nested.sh
