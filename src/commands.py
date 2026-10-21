"""Команды эмулятора: ls, cd, whoami, tree, who, vfs-save, mv.

Каждый обработчик принимает экземпляр Shell и список аргументов.
При ошибке обработчик бросает CommandError - оболочка печатает её
сообщение и продолжает работу.
"""

from src.vfs import Directory, VFSError


class CommandError(Exception):
    """Ошибка выполнения команды (неверные аргументы, путь не найден и т.д.)."""


def _check_args(name: str, args: list[str], minimum: int, maximum: int) -> None:
    if len(args) < minimum:
        raise CommandError(f"недостаточно аргументов для команды '{name}'")
    if len(args) > maximum:
        raise CommandError(f"слишком много аргументов для команды '{name}'")


def _get_dir(shell, path: str) -> Directory:
    """Ищет каталог по пути; бросает CommandError, если пути нет или это файл."""
    try:
        node = shell.vfs.resolve(path, shell.cwd)
    except VFSError as e:
        raise CommandError(str(e))
    if not node.is_dir:
        raise CommandError(f"'{path}' - не каталог")
    return node


def cmd_ls(shell, args: list[str]) -> None:
    """ls [путь] - содержимое текущего или указанного каталога."""
    _check_args("ls", args, 0, 1)
    directory = _get_dir(shell, args[0]) if args else shell.cwd
    for child in directory.sorted_children():
        shell.write(child.name + "/" if child.is_dir else child.name)


def cmd_cd(shell, args: list[str]) -> None:
    """cd путь - смена текущего каталога (поддерживает ., .., /, вложенные пути)."""
    _check_args("cd", args, 1, 1)
    shell.cwd = _get_dir(shell, args[0])  # при ошибке cwd не меняется


def cmd_whoami(shell, args: list[str]) -> None:
    """whoami - имя пользователя эмулятора."""
    _check_args("whoami", args, 0, 0)
    shell.write(shell.user)


def cmd_who(shell, args: list[str]) -> None:
    """who - условная сессия: пользователь и терминал."""
    _check_args("who", args, 0, 0)
    shell.write(f"{shell.user} console")


def _tree_lines(directory: Directory, prefix: str = ""):
    children = directory.sorted_children()
    for i, child in enumerate(children):
        last = i == len(children) - 1
        yield prefix + ("└── " if last else "├── ") + child.name
        if child.is_dir:
            yield from _tree_lines(child, prefix + ("    " if last else "│   "))


def cmd_tree(shell, args: list[str]) -> None:
    """tree [путь] - дерево каталогов и файлов, обход внутренней VFS."""
    _check_args("tree", args, 0, 1)
    directory = _get_dir(shell, args[0]) if args else shell.cwd
    shell.write(".")
    for line in _tree_lines(directory):
        shell.write(line)


def cmd_vfs_save(shell, args: list[str]) -> None:
    """vfs-save путь - сохраняет текущее состояние VFS в каталог на диске."""
    _check_args("vfs-save", args, 1, 1)
    try:
        shell.vfs.save(args[0])
    except VFSError as e:
        raise CommandError(str(e))
    shell.write(f"VFS сохранена в {args[0]}")


def cmd_mv(shell, args: list[str]) -> None:
    """mv источник назначение - перемещение/переименование только в памяти."""
    _check_args("mv", args, 2, 2)
    src_path, dst_path = args
    vfs = shell.vfs

    # 1. Источник
    try:
        src = vfs.resolve(src_path, shell.cwd)
    except VFSError:
        raise CommandError("исходный объект не найден.")
    if src.parent is None:
        raise CommandError("нельзя переместить корневой каталог.")

    # 2. Куда и под каким именем
    try:
        dst = vfs.resolve(dst_path, shell.cwd)
    except VFSError:
        dst = None

    if dst is not None and dst is src:
        raise CommandError("исходный и целевой объекты совпадают.")

    if dst is not None and dst.is_dir:
        new_parent, new_name = dst, src.name  # mv a documents/ -> внутрь каталога
    elif dst is not None:
        raise CommandError("целевой объект уже существует (перезапись запрещена).")
    else:
        # назначение не существует: родитель должен существовать, имя - новое
        stripped = dst_path.rstrip("/")
        if dst_path.endswith("/") or not stripped:
            raise CommandError("целевой каталог не существует.")
        parent_path, _, new_name = stripped.rpartition("/")
        if parent_path == "" and stripped.startswith("/"):
            parent_path = "/"
        if new_name in ("", ".", ".."):
            raise CommandError("недопустимое имя назначения.")
        if parent_path == "":
            new_parent = shell.cwd
        else:
            try:
                parent = vfs.resolve(parent_path, shell.cwd)
            except VFSError:
                raise CommandError("целевой каталог не существует.")
            if not parent.is_dir:
                raise CommandError("целевой путь не является каталогом.")
            new_parent = parent

    # 3. Все проверки ДО изменения дерева
    if src.is_dir and new_parent.is_inside(src):
        raise CommandError("нельзя переместить каталог внутрь самого себя.")
    if new_name in new_parent.children:
        raise CommandError("целевой объект уже существует (перезапись запрещена).")

    # 4. Само перемещение - только внутренние объекты
    src.parent.remove(src.name)
    src.name = new_name
    new_parent.add(src)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "whoami": cmd_whoami,
    "who": cmd_who,
    "tree": cmd_tree,
    "vfs-save": cmd_vfs_save,
    "mv": cmd_mv,
}
