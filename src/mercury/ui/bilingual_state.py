import base64
from collections.abc import Mapping
from typing import Protocol

from PySide6.QtCore import QSettings


class BilingualViewStateStore(Protocol):
    """Local preference contract for each article's last Reader mode."""

    def load(self, article_id: str) -> bool | None:
        ...

    def save(self, article_id: str, visible: bool) -> None:
        ...


class InMemoryBilingualViewStateStore:
    """Deterministic store for tests and dependency-free UI use."""

    def __init__(
        self,
        initial_states: Mapping[str, bool] | None = None,
    ) -> None:
        self._states = {
            str(article_id): bool(visible)
            for article_id, visible in (initial_states or {}).items()
        }

    def load(self, article_id: str) -> bool | None:
        return self._states.get(str(article_id))

    def save(self, article_id: str, visible: bool) -> None:
        self._states[str(article_id)] = bool(visible)


class QSettingsBilingualViewStateStore:
    """Cross-platform local persistence backed by Qt application settings."""

    _KEY_PREFIX = "reader/bilingual-visibility"

    def __init__(self, settings: QSettings | None = None) -> None:
        self._settings = settings or QSettings()

    def load(self, article_id: str) -> bool | None:
        value = self._settings.value(self._key(article_id), None)
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        return str(value).strip().casefold() in {"1", "true", "yes", "on"}

    def save(self, article_id: str, visible: bool) -> None:
        self._settings.setValue(self._key(article_id), bool(visible))
        self._settings.sync()

    @classmethod
    def _key(cls, article_id: str) -> str:
        encoded_id = base64.urlsafe_b64encode(
            str(article_id).encode("utf-8")
        ).decode("ascii").rstrip("=")
        return f"{cls._KEY_PREFIX}/{encoded_id}"
