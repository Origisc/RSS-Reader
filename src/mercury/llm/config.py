from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse


MIN_TIMEOUT_SECONDS = 1.0
MAX_TIMEOUT_SECONDS = 300.0


class ProviderConfigError(ValueError):
    """A user-correctable, provider-neutral configuration error."""


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """User-supplied configuration with its secret excluded from repr."""

    base_url: str = ""
    model: str = ""
    api_key: str = field(default="", repr=False)
    timeout_seconds: float = 30.0

    @property
    def is_configured(self) -> bool:
        return not self.validation_errors()

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        base_url = self.base_url.strip()
        model = self.model.strip()

        if not base_url:
            errors.append("Base URL is required.")
        else:
            parsed_url = urlparse(base_url)

            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                errors.append("Base URL must be a valid HTTP or HTTPS URL.")

        if not model:
            errors.append("Model name is required.")

        if not MIN_TIMEOUT_SECONDS <= self.timeout_seconds <= MAX_TIMEOUT_SECONDS:
            errors.append(
                "Timeout must be between "
                f"{MIN_TIMEOUT_SECONDS:g} and {MAX_TIMEOUT_SECONDS:g} seconds."
            )

        return tuple(errors)

    def require_valid(self) -> "ProviderConfig":
        errors = self.validation_errors()

        if errors:
            raise ProviderConfigError(" ".join(errors))

        return self


class ProviderConfigStore(Protocol):
    """Persistence boundary for Provider configuration."""

    def load(self) -> ProviderConfig | None:
        ...

    def save(self, config: ProviderConfig) -> None:
        ...

    def clear(self) -> None:
        ...


class InMemoryProviderConfigStore:
    """Offline configuration store used by tests and UI development."""

    def __init__(self, initial_config: ProviderConfig | None = None) -> None:
        self._config = initial_config

    def load(self) -> ProviderConfig | None:
        return self._config

    def save(self, config: ProviderConfig) -> None:
        self._config = config

    def clear(self) -> None:
        self._config = None
