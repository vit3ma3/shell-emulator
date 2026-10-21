"""Оболочка: цикл REPL, выполнение стартового скрипта и диспетчеризация команд."""

import sys

from src.commands import COMMANDS, CommandError
from src.parser import parse_command
from src.vfs import VFSError, VirtualFileSystem


class Shell:
    """Состояние оболочки: VFS, текущий каталог, имя пользователя."""

    def __init__(self, vfs: VirtualFileSystem, out=None,
                 user: str = "student", vfs_name: str = "myvfs"):
        self.vfs = vfs
        self.cwd = vfs.root
        self.user = user
        self.vfs_name = vfs_name
        self.out = out if out is not None else sys.stdout

    def write(self, text: str = "") -> None:
        print(text, file=self.out)

    @property
    def prompt(self) -> str:
        return f"{self.vfs_name}:{self.cwd.path()}$ "

    def execute(self, line: str) -> bool:
        """Выполняет одну строку. Возвращает False, если нужно завершить работу."""
        command, args = parse_command(line)

        if not command:
            return True

        if command == "exit":
            if args:
                self.write("Ошибка: слишком много аргументов для команды 'exit'")
                return True
            self.write("Выход из эмулятора.")
            return False

        handler = COMMANDS.get(command)
        if handler is None:
            self.write(f"Ошибка: неизвестная команда '{command}'")
            return True

        try:
            handler(self, args)
        except (CommandError, VFSError) as e:
            self.write(f"Ошибка: {e}")
        return True

    def run_script(self, lines: list[str]) -> None:
        """Выполняет команды из скрипта, показывая приглашение, команду и результат."""
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            self.write(self.prompt + line)
            if not self.execute(line):
                break

    def run_interactive(self) -> None:
        """Интерактивный цикл: читает команды с клавиатуры, пока не будет exit."""
        while True:
            try:
                line = input(self.prompt)
            except EOFError:  # Ctrl+D / конец ввода
                self.write()
                self.write("Выход из эмулятора.")
                break
            except KeyboardInterrupt:  # Ctrl+C
                self.write()
                continue
            if not self.execute(line):
                break
