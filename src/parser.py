"""Разбор строки с командой."""


def parse_command(line: str) -> tuple[str, list[str]]:
    """Разбирает строку и возвращает имя команды и список аргументов.

    Пустая строка (или строка из одних пробелов) даёт ("", []).
    """
    parts = line.strip().split()

    if not parts:
        return "", []

    return parts[0], parts[1:]
