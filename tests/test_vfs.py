import pytest

from src.vfs import Directory, FileNode, VFSError, VirtualFileSystem


@pytest.fixture
def source(tmp_path):
    """Исходный каталог: readme.txt, documents/report.txt, projects/demo/src/main.py"""
    (tmp_path / "documents").mkdir()
    (tmp_path / "projects" / "demo" / "src").mkdir(parents=True)
    (tmp_path / "readme.txt").write_bytes(b"hello\r\nworld")
    (tmp_path / "documents" / "report.txt").write_bytes(b"report")
    (tmp_path / "projects" / "demo" / "src" / "main.py").write_bytes(b"print(1)")
    return tmp_path


def test_load_builds_tree(source):
    vfs = VirtualFileSystem.load(str(source))
    assert set(vfs.root.children) == {"readme.txt", "documents", "projects"}
    main_py = vfs.resolve("projects/demo/src/main.py", vfs.root)
    assert isinstance(main_py, FileNode)
    assert main_py.content == b"print(1)"


def test_content_is_kept_as_bytes(source):
    vfs = VirtualFileSystem.load(str(source))
    assert vfs.root.children["readme.txt"].content == b"hello\r\nworld"


def test_load_missing_path(tmp_path):
    with pytest.raises(VFSError, match="не существует"):
        VirtualFileSystem.load(str(tmp_path / "nope"))


def test_load_file_instead_of_directory(source):
    with pytest.raises(VFSError, match="ожидается каталог"):
        VirtualFileSystem.load(str(source / "readme.txt"))


def test_load_empty_directory(tmp_path):
    vfs = VirtualFileSystem.load(str(tmp_path))
    assert vfs.root.children == {}


def test_resolve_special_components(source):
    vfs = VirtualFileSystem.load(str(source))
    demo = vfs.resolve("projects/demo", vfs.root)
    assert vfs.resolve("..", demo).name == "projects"
    assert vfs.resolve(".", demo) is demo
    assert vfs.resolve("/", demo) is vfs.root
    assert vfs.resolve("/documents", demo).name == "documents"
    assert vfs.resolve("..", vfs.root) is vfs.root  # выше корня не уходим


def test_resolve_missing(source):
    vfs = VirtualFileSystem.load(str(source))
    with pytest.raises(VFSError):
        vfs.resolve("documents/missing", vfs.root)


def test_resolve_through_file(source):
    vfs = VirtualFileSystem.load(str(source))
    with pytest.raises(VFSError):
        vfs.resolve("readme.txt/x", vfs.root)


def test_node_path(source):
    vfs = VirtualFileSystem.load(str(source))
    assert vfs.root.path() == "/"
    assert vfs.resolve("projects/demo", vfs.root).path() == "/projects/demo"


def test_save_roundtrip(source, tmp_path_factory):
    vfs = VirtualFileSystem.load(str(source))
    target = tmp_path_factory.mktemp("out") / "snapshot"
    vfs.save(str(target))
    assert (target / "readme.txt").read_bytes() == b"hello\r\nworld"
    assert (target / "documents" / "report.txt").read_bytes() == b"report"
    assert (target / "projects" / "demo" / "src" / "main.py").read_bytes() == b"print(1)"


def test_save_existing_target_is_error(source, tmp_path_factory):
    vfs = VirtualFileSystem.load(str(source))
    target = tmp_path_factory.mktemp("out")
    with pytest.raises(VFSError, match="уже существует"):
        vfs.save(str(target))


def test_save_unwritable_target(source):
    vfs = VirtualFileSystem.load(str(source))
    # родитель - файл, создать каталог внутри него нельзя
    with pytest.raises(VFSError):
        vfs.save(str(source / "readme.txt" / "snapshot"))


def test_memory_changes_do_not_touch_disk(source):
    vfs = VirtualFileSystem.load(str(source))
    vfs.root.remove("readme.txt")
    vfs.root.add(Directory("new"))
    assert (source / "readme.txt").exists()
    assert not (source / "new").exists()
