"""Виртуальная файловая система (VFS), которая целиком живёт в памяти.

Исходный каталог на диске читается один раз при загрузке. Дальше все
команды эмулятора работают только с деревом объектов в памяти.
Запись на диск выполняет только VirtualFileSystem.save() (команда vfs-save).
"""

import os
import shutil


class VFSError(Exception):
    """Ошибка при работе с VFS (загрузка, сохранение, разбор пути)."""


class Node:
    """Общий предок для файлов и каталогов."""

    is_dir = False

    def __init__(self, name: str, parent: "Directory | None" = None):
        self.name = name
        self.parent = parent

    def path(self) -> str:
        """Абсолютный путь объекта внутри VFS (корень - '/')."""
        parts = []
        node = self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))


class FileNode(Node):
    """Файл: имя и содержимое в байтах (кодировка и переводы строк не меняются)."""

    def __init__(self, name: str, content: bytes = b"", parent: "Directory | None" = None):
        super().__init__(name, parent)
        self.content = content


class Directory(Node):
    """Каталог: имя, родитель и словарь дочерних объектов."""

    is_dir = True

    def __init__(self, name: str, parent: "Directory | None" = None):
        super().__init__(name, parent)
        self.children: dict[str, Node] = {}

    def add(self, node: Node) -> None:
        """Добавляет объект в каталог и выставляет ему родителя."""
        if node.name in self.children:
            raise VFSError(f"объект '{node.name}' уже существует")
        node.parent = self
        self.children[node.name] = node

    def remove(self, name: str) -> Node:
        """Убирает объект из каталога (только в памяти) и возвращает его."""
        node = self.children.pop(name)
        node.parent = None
        return node

    def sorted_children(self) -> list[Node]:
        """Дочерние объекты, отсортированные по имени."""
        return sorted(self.children.values(), key=lambda n: (n.name.lower(), n.name))

    def is_inside(self, other: "Directory") -> bool:
        """True, если self совпадает с other или лежит внутри other."""
        node: Directory | None = self
        while node is not None:
            if node is other:
                return True
            node = node.parent
        return False


class VirtualFileSystem:
    """Дерево каталогов и файлов в памяти."""

    def __init__(self, root: Directory | None = None):
        self.root = root if root is not None else Directory("")

    # ---------- загрузка ----------

    @classmethod
    def load(cls, source: str) -> "VirtualFileSystem":
        """Загружает каталог с диска в память (рекурсивно)."""
        if not os.path.exists(source):
            raise VFSError("указанный путь не существует.")
        if not os.path.isdir(source):
            raise VFSError("ожидается каталог.")

        root = Directory("")
        cls._load_dir(source, root)
        return cls(root)

    @classmethod
    def _load_dir(cls, path: str, directory: Directory) -> None:
        try:
            with os.scandir(path) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError as e:
            raise VFSError(f"не удалось прочитать каталог '{path}': {e.strerror}")

        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                child = Directory(entry.name)
                directory.add(child)
                cls._load_dir(entry.path, child)
            else:
                try:
                    with open(entry.path, "rb") as f:
                        data = f.read()
                except OSError as e:
                    raise VFSError(f"не удалось загрузить файл '{entry.path}': {e.strerror}")
                directory.add(FileNode(entry.name, data))

    # ---------- пути ----------

    def resolve(self, path: str, cwd: Directory) -> Node:
        """Находит объект по абсолютному или относительному пути.

        Поддерживаются '/', '.', '..' и вложенные пути (projects/demo).
        '..' в корне оставляет в корне.
        """
        if not path:
            raise VFSError("пустой путь")

        node: Node = self.root if path.startswith("/") else cwd

        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                node = node.parent if node.parent is not None else node
                continue
            if not node.is_dir:
                raise VFSError(f"'{node.name}' не является каталогом (путь '{path}')")
            child = node.children.get(part)
            if child is None:
                raise VFSError(f"путь не найден: '{path}'")
            node = child

        return node

    # ---------- сохранение ----------

    def save(self, target: str) -> None:
        """Сохраняет текущее состояние VFS в каталог на диске.

        Формат такой же, как у исходной VFS: обычные каталоги и файлы.
        Существующий путь не перезаписывается.
        """
        if os.path.lexists(target):
            raise VFSError(f"место назначения уже существует: '{target}'")

        try:
            os.makedirs(target)
        except OSError as e:
            raise VFSError(f"не удалось создать '{target}': {e.strerror}")

        try:
            self._write_dir(self.root, target)
        except OSError as e:
            shutil.rmtree(target, ignore_errors=True)  # убираем только что созданное
            raise VFSError(f"ошибка записи в '{target}': {e.strerror}")

    def _write_dir(self, directory: Directory, disk_path: str) -> None:
        for child in directory.children.values():
            child_path = os.path.join(disk_path, child.name)
            if child.is_dir:
                os.mkdir(child_path)
                self._write_dir(child, child_path)
            else:
                with open(child_path, "wb") as f:
                    f.write(child.content)
