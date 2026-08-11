"""Tests for historical impact path mapping."""

from intentinsight.domain.services.historical_impact_mapper import (
    module_to_package,
    path_to_module,
)


def test_path_to_module_maps_python_file() -> None:
    assert path_to_module("flask/helpers.py") == (
        "flask.helpers"
    )


def test_path_to_module_maps_package_initializer() -> None:
    assert path_to_module("flask/__init__.py") == "flask"


def test_path_to_module_maps_nested_python_file() -> None:
    assert path_to_module(
        "flask/tests/test_basic.py"
    ) == "flask.tests.test_basic"


def test_path_to_module_maps_pyi_file() -> None:
    assert path_to_module(
        "flask/typing.pyi"
    ) == "flask.typing"


def test_path_to_module_ignores_non_python_file() -> None:
    assert path_to_module("README") is None
    assert path_to_module("docs/index.rst") is None
    assert path_to_module("static/logo.png") is None


def test_module_to_package_returns_parent_package() -> None:
    assert module_to_package("flask.helpers") == "flask"


def test_module_to_package_handles_top_level_module() -> None:
    assert module_to_package("setup") == "setup"