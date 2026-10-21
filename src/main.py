"""Точка входа: разбор параметров запуска, загрузка VFS, запуск оболочки."""

import argparse
import sys
from pathlib import Path

# Чтобы работал и запуск `python src/main.py`, и `python -m src.main`
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.shell import Shell
from src.vfs import VFSError, VirtualFileSystem


def parse_args(argv=None):
    """Разбирает параметры запуска приложения."""
    parser = argparse.ArgumentParser(
        description="Эмулятор командной оболочки с виртуальной файловой системой"
    )
    parser.add_argument("--vfs", required=True,
                        help="путь к каталогу с исходной VFS")
    parser.add_argument("--script",
                        help="путь к стартовому скрипту с командами эмулятора")
    return parser.parse_args(argv)


def print_params(args) -> None:
    """Отладочный вывод всех заданных параметров."""
    print("Параметры запуска:")
    print(f"  VFS: {args.vfs}")
    if args.script:
        print(f"  Скрипт: {args.script}")
    else:
        print("  Скрипт: не указан (интерактивный режим без стартового сценария)")


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # корректная кириллица в консоли Windows
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    args = parse_args(argv)
    print_params(args)

    try:
        vfs = VirtualFileSystem.load(args.vfs)
    except VFSError as e:
        print(f"Ошибка VFS: {e}", file=sys.stderr)
        return 1

    script_lines = None
    if args.script:
        try:
            with open(args.script, encoding="utf-8-sig") as f:
                script_lines = f.read().splitlines()
        except (OSError, UnicodeDecodeError) as e:
            reason = getattr(e, "strerror", None) or str(e)
            print(f"Ошибка скрипта: не удалось прочитать '{args.script}': {reason}",
                  file=sys.stderr)
            return 1

    shell = Shell(vfs)
    if script_lines is not None:
        shell.run_script(script_lines)
    else:
        shell.run_interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
