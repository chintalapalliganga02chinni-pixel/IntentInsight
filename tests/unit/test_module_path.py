"""Tests for path-derived structural module identities."""

from intentinsight.analysis.structural.module_path import (
    filename_to_module,
    normalize_filename,
)


def test_filename_normalization() -> None:
    """Repository paths should use normalized separators."""

    assert normalize_filename(
        "./flask\\app.py"
    ) == "flask/app.py"


def test_python_file_becomes_module() -> None:
    """Python source paths should become dotted modules."""

    assert filename_to_module(
        "flask/app.py"
    ) == "flask.app"


def test_python_package_init_becomes_package() -> None:
    """__init__.py should map to its containing package."""

    assert filename_to_module(
        "flask/testsuite/__init__.py"
    ) == "flask.testsuite"


def test_non_python_file_remains_path_derived() -> None:
    """Non-Python files should still receive structural identities."""

    assert filename_to_module(
        "docs/views.rst"
    ) == "docs.views"