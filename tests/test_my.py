import sys
import pytest
from conftest import load

M = load(5)


def test_single_command_exit_code():
    """Тест виконання однієї команди конвеєра з перевіркою ненульового коду."""
    res = M.run_pipeline([[sys.executable, "tests/filters.py", "exit", "42"]])
    assert res == [42]


def test_pipeline_stdout_file(tmp_path):
    """Тест запису останнього етапу конвеєра у вказаний файл."""
    out_file = tmp_path / "result.txt"
    stages = [
        [sys.executable, "tests/filters.py", "words", "banana", "apple", "cherry"],
        [sys.executable, "tests/filters.py", "sort"],
    ]
    res = M.run_pipeline(stages, stdout_path=str(out_file))
    assert res == [0, 0]
    assert out_file.read_text() == "apple\nbanana\ncherry\n"


def test_empty_stages_list():
    """Тест крайового випадку з порожнім списком етапів."""
    assert M.run_pipeline([]) == []


def test_pipeline_with_middle_stage_failure():
    """Тест передачі статусів при аварійному завершенні проміжного етапу."""
    stages = [
        [sys.executable, "tests/filters.py", "gen", "3"],
        [sys.executable, "tests/filters.py", "fail", "5"],
        [sys.executable, "tests/filters.py", "count"],
    ]
    res = M.run_pipeline(stages)
    assert res == [0, 5, 0]