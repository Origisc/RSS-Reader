from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

APP_DIRECTORY_NAME = "Mercury"
DATABASE_FILE_NAME = "database.db"
DATA_DIRECTORY_ENVIRONMENT_VARIABLE = "MERCURY_DATA_DIR"


def application_data_directory(
    *,
    environment: Mapping[str, str] | None = None,
    platform: str | None = None,
    home: Path | None = None,
) -> Path:
    """Return Mercury's writable, per-user data directory."""

    environment = os.environ if environment is None else environment
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else Path(home)

    override = environment.get(
        DATA_DIRECTORY_ENVIRONMENT_VARIABLE,
        "",
    ).strip()
    if override:
        return Path(override).expanduser()

    if platform == "win32":
        base_directory = (
            environment.get("LOCALAPPDATA")
            or environment.get("APPDATA")
        )
        base = (
            Path(base_directory)
            if base_directory
            else home / "AppData" / "Local"
        )
    elif platform == "darwin":
        base = home / "Library" / "Application Support"
    else:
        xdg_data_home = environment.get("XDG_DATA_HOME", "").strip()
        base = Path(xdg_data_home) if xdg_data_home else home / ".local" / "share"

    return base / APP_DIRECTORY_NAME


def database_path(
    *,
    legacy_paths: Iterable[Path] = (),
    environment: Mapping[str, str] | None = None,
    platform: str | None = None,
    home: Path | None = None,
) -> Path:
    """Create the app data directory and return the local database path.

    The first existing legacy database is copied only when the destination
    database does not exist. Existing user data is never overwritten.
    """

    data_directory = application_data_directory(
        environment=environment,
        platform=platform,
        home=home,
    )
    data_directory.mkdir(parents=True, exist_ok=True)
    destination = data_directory / DATABASE_FILE_NAME

    if destination.exists():
        return destination

    destination_resolved = destination.resolve()
    for candidate in legacy_paths:
        candidate = Path(candidate)
        if not candidate.is_file():
            continue
        if candidate.resolve() == destination_resolved:
            continue
        shutil.copy2(candidate, destination)
        break

    return destination
