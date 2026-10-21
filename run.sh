#!/usr/bin/env bash
# Запуск эмулятора: ./run.sh --vfs examples/vfs/nested [--script scripts/stage2.sh]
cd "$(dirname "$0")"
exec "${PYTHON:-python}" -m src.main "$@"
