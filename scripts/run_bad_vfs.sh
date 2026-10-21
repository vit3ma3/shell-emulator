#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python}"

# несуществующий путь и файл вместо каталога (код возврата 1 ожидаем)
"$PYTHON" -m src.main --vfs examples/vfs/does_not_exist || true
"$PYTHON" -m src.main --vfs README.md || true
# не указан обязательный --vfs
"$PYTHON" -m src.main --script scripts/stage2.sh || true
