from dataclasses import dataclass

from mercury.llm import ProviderConfig


CUSTOM_PRESET_ID = "custom"


@dataclass(frozen=True, slots=True)
class ProviderPreset:
    """Editable UI template for a Provider-neutral configuration."""

    identifier: str
    name_key: str
    description_key: str
    config: ProviderConfig | None = None


PROVIDER_PRESETS = (
    ProviderPreset(
        identifier=CUSTOM_PRESET_ID,
        name_key="ai_settings.preset.custom",
        description_key="ai_settings.preset.custom_description",
    ),
    ProviderPreset(
        identifier="ollama-local-qwen25-7b",
        name_key="ai_settings.preset.ollama_qwen25_7b",
        description_key=(
            "ai_settings.preset.ollama_qwen25_7b_description"
        ),
        config=ProviderConfig(
            base_url="http://127.0.0.1:11434/v1",
            model="qwen2.5:7b-instruct",
            timeout_seconds=120.0,
        ),
    ),
    ProviderPreset(
        identifier="ollama-local-deepseek",
        name_key="ai_settings.preset.ollama_deepseek",
        description_key="ai_settings.preset.ollama_deepseek_description",
        config=ProviderConfig(
            base_url="http://127.0.0.1:11434/v1",
            model="deepseek-r1:1.5b",
            timeout_seconds=120.0,
        ),
    ),
    ProviderPreset(
        identifier="deepseek-api",
        name_key="ai_settings.preset.deepseek_api",
        description_key="ai_settings.preset.deepseek_api_description",
        config=ProviderConfig(
            base_url="https://api.deepseek.com",
            model="deepseek-v4-flash",
            timeout_seconds=60.0,
        ),
    ),
)


def find_matching_preset(config: ProviderConfig) -> ProviderPreset:
    """Return a concrete preset only when endpoint and model still match."""

    normalized_url = config.base_url.strip().rstrip("/")
    normalized_model = config.model.strip()

    for preset in PROVIDER_PRESETS:
        preset_config = preset.config
        if preset_config is None:
            continue

        if (
            normalized_url
            == preset_config.base_url.strip().rstrip("/")
            and normalized_model == preset_config.model.strip()
        ):
            return preset

    return PROVIDER_PRESETS[0]


def preset_by_id(identifier: str) -> ProviderPreset:
    for preset in PROVIDER_PRESETS:
        if preset.identifier == identifier:
            return preset

    return PROVIDER_PRESETS[0]
