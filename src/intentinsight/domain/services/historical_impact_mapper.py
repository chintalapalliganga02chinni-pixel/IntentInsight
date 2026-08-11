"""Map changed repository paths to structural modules and packages."""

from __future__ import annotations

from pathlib import PurePosixPath


def path_to_module(filename: str) -> str | None:
    """Convert a repository file path into a structural module name."""

    path = PurePosixPath(filename)

    if path.suffix not in {".py", ".pyi"}:
        return None

    parts = list(path.parts)

    if not parts:
        return None

    filename_part = parts[-1]

    if filename_part in {"__init__.py", "__init__.pyi"}:
        module_parts = parts[:-1]

        if not module_parts:
            return None

        return ".".join(module_parts)

    module_parts = parts[:-1] + [
        path.stem,
    ]

    return ".".join(module_parts)


def module_to_package(module: str) -> str:
    """Return the package portion of a module name."""

    parts = module.split(".")

    if len(parts) <= 1:
        return module

    return ".".join(parts[:-1])