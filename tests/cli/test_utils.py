from pathlib import Path

import pytest
from typer import Exit

from autosubs.cli.utils import PathProcessor, SupportedExtension


def test_path_processor_single_file(tmp_path: Path) -> None:
    """Test processing a single valid file."""
    in_file = tmp_path / "test.mp4"
    in_file.touch()
    processor = PathProcessor(in_file, None, SupportedExtension.MEDIA)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_file, in_file)


def test_path_processor_single_file_with_output(tmp_path: Path) -> None:
    """Test processing a single file with a specified output path."""
    in_file = tmp_path / "test.mp4"
    out_file = tmp_path / "output.srt"
    in_file.touch()
    processor = PathProcessor(in_file, out_file, SupportedExtension.MEDIA)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_file, out_file)


def test_path_processor_unsupported_file_type(tmp_path: Path) -> None:
    """Test that an unsupported file type raises an Exit exception."""
    in_file = tmp_path / "test.txt"
    in_file.touch()
    processor = PathProcessor(in_file, None, SupportedExtension.MEDIA)
    with pytest.raises(Exit):
        list(processor.process())


def test_path_processor_directory(tmp_path: Path) -> None:
    """Test processing a directory of files."""
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    (in_dir / "test1.json").touch()
    (in_dir / "test2.json").touch()
    (in_dir / "ignored.txt").touch()

    processor = PathProcessor(in_dir, None, SupportedExtension.JSON)
    results = list(processor.process())
    assert len(results) == 2
    assert results[0] == (in_dir / "test1.json", in_dir / "test1.json")
    assert results[1] == (in_dir / "test2.json", in_dir / "test2.json")


def test_path_processor_directory_with_output_dir(tmp_path: Path) -> None:
    """Test processing a directory with a specified output directory."""
    in_dir = tmp_path / "input"
    out_dir = tmp_path / "output"
    in_dir.mkdir()
    out_dir.mkdir()
    (in_dir / "test1.json").touch()

    processor = PathProcessor(in_dir, out_dir, SupportedExtension.JSON)
    results = list(processor.process())
    assert len(results) == 1
    assert results[0] == (in_dir / "test1.json", out_dir / "test1.json")


def test_path_processor_empty_directory(tmp_path: Path) -> None:
    """Test that an empty directory raises an Exit exception."""
    in_dir = tmp_path / "input"
    in_dir.mkdir()
    processor = PathProcessor(in_dir, None, SupportedExtension.JSON)
    with pytest.raises(Exit):
        list(processor.process())


def test_path_processor_input_dir_output_file_error(tmp_path: Path) -> None:
    """Test that input dir with output file raises an Exit exception."""
    in_dir = tmp_path / "input"
    out_file = tmp_path / "output.txt"
    in_dir.mkdir()
    out_file.touch()

    with pytest.raises(Exit):
        PathProcessor(in_dir, out_file, SupportedExtension.JSON)
