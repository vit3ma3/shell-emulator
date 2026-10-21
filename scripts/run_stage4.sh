#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python}"

rm -rf output/stage4_snapshot
"$PYTHON" -m src.main --vfs examples/vfs/nested --script scripts/stage4.sh
