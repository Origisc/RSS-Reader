import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.llm.provider import LLMResult, MockProvider, OpenAICompatibleProvider, create_provider


class TestMockProvider(unittest.TestCase):
    def test_chat_returns_success(self):
        provider = MockProvider()
        messages = [{"role": "user", "content": "Hello"}]
        result = provider.chat(messages)

        self.assertTrue(result.success)
        self.assertIn("mock translation", result.content.lower())

    def test_chat_returns_custom_response(self):
        custom_response = "Custom mock response"
        provider = MockProvider(mock_response=custom_response)
        messages = [{"role": "user", "content": "Hello"}]
        result = provider.chat(messages)

        self.assertTrue(result.success)
        self.assertEqual(result.content, custom_response)

    def test_get_name(self):
        provider = MockProvider()
        self.assertEqual(provider.get_name(), "MockProvider")


class TestOpenAICompatibleProvider(unittest.TestCase):
    def test_chat_success(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"choices": [{"message": {"content": "Translated text"}}]}'
            mock_urlopen.return_value.__enter__.return_value = mock_response

            provider = OpenAICompatibleProvider(
                base_url="https://api.example.com",
                api_key="test-key",
                model="test-model",
            )
            messages = [{"role": "user", "content": "Hello"}]
            result = provider.chat(messages)

            self.assertTrue(result.success)
            self.assertEqual(result.content, "Translated text")

    def test_chat_http_error(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("HTTP error: 401")

            provider = OpenAICompatibleProvider(
                base_url="https://api.example.com",
                api_key="test-key",
            )
            messages = [{"role": "user", "content": "Hello"}]
            result = provider.chat(messages)

            self.assertFalse(result.success)
            self.assertIn("error", result.error_message.lower())

    def test_chat_timeout(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = TimeoutError()

            provider = OpenAICompatibleProvider(
                base_url="https://api.example.com",
                api_key="test-key",
                timeout=1,
            )
            messages = [{"role": "user", "content": "Hello"}]
            result = provider.chat(messages)

            self.assertFalse(result.success)
            self.assertIn("timeout", result.error_message.lower())

    def test_get_name(self):
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com",
            api_key="test-key",
        )
        self.assertEqual(provider.get_name(), "OpenAICompatibleProvider")


class TestCreateProvider(unittest.TestCase):
    def test_create_mock_provider_by_default(self):
        config = {}
        provider = create_provider(config)
        self.assertIsInstance(provider, MockProvider)

    def test_create_mock_provider_explicit(self):
        config = {"type": "mock", "mock_response": "Custom"}
        provider = create_provider(config)
        self.assertIsInstance(provider, MockProvider)

    def test_create_openai_provider(self):
        config = {
            "type": "openai",
            "base_url": "https://api.example.com",
            "api_key": "test-key",
            "model": "gpt-4",
            "timeout": 30,
        }
        provider = create_provider(config)
        self.assertIsInstance(provider, OpenAICompatibleProvider)


if __name__ == "__main__":
    unittest.main()