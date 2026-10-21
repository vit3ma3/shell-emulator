import io

import pytest

from src.shell import Shell
from src.vfs import Directory, FileNode, VirtualFileSystem


def make_vfs() -> VirtualFileSystem:
    """/
    ├── documents/ (notes.txt, report.txt)
    ├── empty/
    ├── projects/demo/main.py
    └── readme.txt
    """
    root = Directory("")
    documents = Directory("documents")
    root.add(documents)
    documents.add(FileNode("notes.txt", b"n"))
    documents.add(FileNode("report.txt", b"r"))
    root.add(Directory("empty"))
    projects = Directory("projects")
    root.add(projects)
    demo = Directory("demo")
    projects.add(demo)
    demo.add(FileNode("main.py", b"print()"))
    root.add(FileNode("readme.txt", b"readme"))
    return VirtualFileSystem(root)


@pytest.fixture
def shell():
    return Shell(make_vfs(), out=io.StringIO())


def run(shell, *lines):
    """Выполняет команды и возвращает накопленный вывод."""
    for line in lines:
        shell.execute(line)
    text = shell.out.getvalue()
    shell.out.truncate(0)
    shell.out.seek(0)
    return text


# ---------- общие ----------

def test_unknown_command(shell):
    assert run(shell, "hello") == "Ошибка: неизвестная команда 'hello'\n"


def test_empty_line_does_nothing(shell):
    assert run(shell, "", "   ") == ""


def test_exit_stops(shell):
    assert shell.execute("exit") is False
    assert "Выход из эмулятора." in shell.out.getvalue()


def test_prompt_changes_with_cwd(shell):
    assert shell.prompt == "myvfs:/$ "
    run(shell, "cd documents")
    assert shell.prompt == "myvfs:/documents$ "


# ---------- ls ----------

def test_ls_root(shell):
    assert run(shell, "ls") == "documents/\nempty/\nprojects/\nreadme.txt\n"


def test_ls_path(shell):
    assert run(shell, "ls documents") == "notes.txt\nreport.txt\n"


def test_ls_absolute_root(shell):
    run(shell, "cd documents")
    assert run(shell, "ls /") == "documents/\nempty/\nprojects/\nreadme.txt\n"


def test_ls_empty_directory(shell):
    assert run(shell, "ls empty") == ""


def test_ls_errors(shell):
    assert run(shell, "ls missing").startswith("Ошибка:")
    assert run(shell, "ls readme.txt").startswith("Ошибка:")
    assert run(shell, "ls a b").startswith("Ошибка:")


# ---------- cd ----------

def test_cd_forward_and_back(shell):
    run(shell, "cd projects/demo")
    assert shell.cwd.path() == "/projects/demo"
    run(shell, "cd ..")
    assert shell.cwd.path() == "/projects"
    run(shell, "cd /")
    assert shell.cwd.path() == "/"
    run(shell, "cd documents", "cd .")
    assert shell.cwd.path() == "/documents"


def test_cd_error_keeps_cwd(shell):
    run(shell, "cd documents")
    assert run(shell, "cd missing").startswith("Ошибка:")
    assert run(shell, "cd ../readme.txt").startswith("Ошибка:")
    assert run(shell, "cd").startswith("Ошибка:")
    assert run(shell, "cd a b").startswith("Ошибка:")
    assert shell.cwd.path() == "/documents"


def test_cd_missing_nested_keeps_cwd(shell):
    run(shell, "cd documents/missing")
    assert shell.cwd.path() == "/"


# ---------- whoami / who ----------

def test_whoami(shell):
    assert run(shell, "whoami") == "student\n"


def test_who(shell):
    assert run(shell, "who") == "student console\n"


def test_whoami_who_reject_arguments(shell):
    assert run(shell, "whoami x").startswith("Ошибка:")
    assert run(shell, "who x").startswith("Ошибка:")


# ---------- tree ----------

def test_tree_root(shell):
    expected = (
        ".\n"
        "├── documents\n"
        "│   ├── notes.txt\n"
        "│   └── report.txt\n"
        "├── empty\n"
        "├── projects\n"
        "│   └── demo\n"
        "│       └── main.py\n"
        "└── readme.txt\n"
    )
    assert run(shell, "tree") == expected


def test_tree_from_current_directory(shell):
    run(shell, "cd projects")
    assert run(shell, "tree") == ".\n└── demo\n    └── main.py\n"


def test_tree_with_path_and_empty_dir(shell):
    assert run(shell, "tree empty") == ".\n"
    assert run(shell, "tree documents") == ".\n├── notes.txt\n└── report.txt\n"


def test_tree_errors(shell):
    assert run(shell, "tree missing").startswith("Ошибка:")
    assert run(shell, "tree readme.txt").startswith("Ошибка:")


# ---------- mv ----------

def test_mv_rename(shell):
    run(shell, "mv readme.txt intro.txt")
    assert "intro.txt" in shell.vfs.root.children
    assert "readme.txt" not in shell.vfs.root.children


def test_mv_into_directory(shell):
    run(shell, "mv readme.txt documents/")
    assert "readme.txt" not in shell.vfs.root.children
    assert "readme.txt" in shell.vfs.root.children["documents"].children
    assert shell.vfs.root.children["documents"].children["readme.txt"].parent.name == "documents"


def test_mv_into_directory_without_slash(shell):
    run(shell, "mv readme.txt documents")
    assert "readme.txt" in shell.vfs.root.children["documents"].children


def test_mv_with_rename(shell):
    run(shell, "mv readme.txt documents/intro.txt")
    assert "intro.txt" in shell.vfs.root.children["documents"].children
    assert "readme.txt" not in shell.vfs.root.children


def test_mv_directory(shell):
    run(shell, "mv empty documents/")
    assert "empty" in shell.vfs.root.children["documents"].children


def test_mv_errors_leave_vfs_unchanged(shell):
    before = run(shell, "tree")
    assert run(shell, "mv missing.txt notes.txt") == "Ошибка: исходный объект не найден.\n"
    assert run(shell, "mv").startswith("Ошибка:")
    assert run(shell, "mv readme.txt").startswith("Ошибка:")
    assert run(shell, "mv readme.txt a b").startswith("Ошибка:")
    assert run(shell, "mv readme.txt missing/").startswith("Ошибка:")
    assert run(shell, "mv readme.txt missing/x.txt").startswith("Ошибка:")
    assert run(shell, "mv readme.txt documents/notes.txt").startswith("Ошибка:")  # перезапись
    assert run(shell, "mv projects projects/demo").startswith("Ошибка:")  # внутрь себя
    assert run(shell, "mv projects projects").startswith("Ошибка:")
    assert run(shell, "mv / documents").startswith("Ошибка:")  # корень
    assert run(shell, "mv readme.txt documents/notes.txt/x").startswith("Ошибка:")
    assert run(shell, "tree") == before


def test_mv_does_not_touch_disk(tmp_path):
    (tmp_path / "test.txt").write_text("x")
    vfs = VirtualFileSystem.load(str(tmp_path))
    shell = Shell(vfs, out=io.StringIO())
    shell.execute("mv test.txt renamed.txt")
    assert (tmp_path / "test.txt").exists()
    assert not (tmp_path / "renamed.txt").exists()


# ---------- vfs-save ----------

def test_vfs_save_saves_changed_state(shell, tmp_path):
    run(shell, "mv readme.txt intro.txt")
    target = tmp_path / "snap"
    assert run(shell, f"vfs-save {target}") == f"VFS сохранена в {target}\n"
    assert (target / "intro.txt").read_bytes() == b"readme"
    assert not (target / "readme.txt").exists()
    assert (target / "projects" / "demo" / "main.py").exists()
    assert (target / "empty").is_dir()


def test_vfs_save_argument_errors(shell):
    assert run(shell, "vfs-save").startswith("Ошибка:")
    assert run(shell, "vfs-save a b").startswith("Ошибка:")


def test_vfs_save_existing_target(shell, tmp_path):
    assert run(shell, f"vfs-save {tmp_path}").startswith("Ошибка:")


# ---------- скрипт ----------

def test_script_skips_comments_and_stops_on_exit(shell):
    shell.run_script(["# комментарий", "", "ls documents", "exit", "ls"])
    out = shell.out.getvalue()
    assert out == (
        "myvfs:/$ ls documents\n"
        "notes.txt\n"
        "report.txt\n"
        "myvfs:/$ exit\n"
        "Выход из эмулятора.\n"
    )
