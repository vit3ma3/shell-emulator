#!/usr/bin/env bash
# Проверка изоляции: mv меняет только память, vfs-save сохраняет изменённое состояние.
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/source"
echo "hello" > "$TMP/source/test.txt"

# 1) mv без сохранения: исходник на диске не должен измениться
printf 'mv test.txt renamed.txt\nls\nexit\n' > "$TMP/no_save.sh"
"$PYTHON" -m src.main --vfs "$TMP/source" --script "$TMP/no_save.sh"
if [ -f "$TMP/source/test.txt" ] && [ ! -e "$TMP/source/renamed.txt" ]; then
  echo "OK: исходный test.txt остался на диске"
else
  echo "FAIL: исходный каталог изменился"; exit 1
fi

# 2) mv + vfs-save: в снимке должно быть изменённое состояние
printf 'mv test.txt renamed.txt\nvfs-save %s/snapshot\nexit\n' "$TMP" > "$TMP/with_save.sh"
"$PYTHON" -m src.main --vfs "$TMP/source" --script "$TMP/with_save.sh"
if [ -f "$TMP/snapshot/renamed.txt" ] && [ ! -e "$TMP/snapshot/test.txt" ] \
   && [ -f "$TMP/source/test.txt" ]; then
  echo "OK: снимок содержит renamed.txt, исходник не тронут"
else
  echo "FAIL: снимок или исходник неверны"; exit 1
fi
