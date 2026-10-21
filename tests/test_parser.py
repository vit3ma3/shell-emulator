from src.parser import parse_command


def test_command_without_arguments():
    assert parse_command("ls") == ("ls", [])


def test_command_with_one_argument():
    assert parse_command("cd documents") == ("cd", ["documents"])


def test_command_with_several_arguments():
    assert parse_command("mv a b") == ("mv", ["a", "b"])


def test_empty_command():
    assert parse_command("") == ("", [])


def test_spaces_only():
    assert parse_command("    ") == ("", [])


def test_extra_spaces_are_ignored():
    assert parse_command("   cd    documents  ") == ("cd", ["documents"])
