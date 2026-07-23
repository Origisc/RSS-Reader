from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional
import json
import os


@dataclass
class LLMConfig:
    provider_type: str = "mock"
    base_url: str = ""
    api_key: str = ""
    model: str = "gpt-3.5-turbo"
    timeout: int = 15
    mock_response: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "LLMConfig":
        return cls(**data)


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_dir = os.path.expanduser("~/.mercury")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "llm_config.json")
        self._config_path = config_path

    def load(self) -> LLMConfig:
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return LLMConfig.from_dict(data)
        except Exception:
            pass
        return LLMConfig()

    def save(self, config: LLMConfig) -> bool:
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def get_provider_config(self) -> dict:
        config = self.load()
        return {
            "type": config.provider_type,
            "base_url": config.base_url,
            "api_key": config.api_key,
            "model": config.model,
            "timeout": config.timeout,
            "mock_response": config.mock_response,
        }


DEFAULT_CONFIG = LLMConfig()

_config_manager = ConfigManager()


def get_config() -> LLMConfig:
    return _config_manager.load()


def save_config(config: LLMConfig) -> bool:
    return _config_manager.save(config)