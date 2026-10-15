import unittest
from unittest.mock import patch

import llm_client


class CreateLlmClientTests(unittest.TestCase):
    def test_mono_reads_key_from_environment(self):
        with (
            patch("llm_client.OpenAI") as openai,
            patch("llm_client.load_dotenv") as load_dotenv,
            patch(
                "llm_client.os.getenv", return_value="mono-test-key"
            ) as getenv,
        ):
            client, model = llm_client.create_llm_client("mono")

        self.assertIs(client, openai.return_value)
        self.assertEqual(model, "gpt-5.5")
        openai.assert_called_once_with(
            base_url=llm_client.MONO_BASE_URL,
            api_key="mono-test-key",
        )
        load_dotenv.assert_called_once_with()
        getenv.assert_called_once_with("MY_API_KEY")

    @patch("llm_client.OpenAI")
    def test_ollama_uses_local_endpoint_without_loading_dotenv(self, openai):
        with patch("llm_client.load_dotenv") as load_dotenv:
            client, model = llm_client.create_llm_client("ollama")

        self.assertIs(client, openai.return_value)
        self.assertEqual(model, "llama3.2:3b")
        openai.assert_called_once_with(
            base_url=llm_client.OLLAMA_BASE_URL,
            api_key="ollama",
        )
        load_dotenv.assert_not_called()

    def test_mono_requires_an_api_key(self):
        with (
            patch("llm_client.load_dotenv"),
            patch("llm_client.os.getenv", return_value=None),
        ):
            with self.assertRaisesRegex(ValueError, "MY_API_KEY"):
                llm_client.create_llm_client("mono")

    def test_custom_api_key_environment_variable_can_be_used(self):
        with (
            patch("llm_client.load_dotenv"),
            patch(
                "llm_client.os.getenv", return_value="custom-test-key"
            ) as getenv,
            patch("llm_client.OpenAI") as openai,
        ):
            llm_client.create_llm_client(
                "mono", api_key_env="CUSTOM_LLM_KEY"
            )

        getenv.assert_called_once_with("CUSTOM_LLM_KEY")
        openai.assert_called_once_with(
            base_url=llm_client.MONO_BASE_URL,
            api_key="custom-test-key",
        )

    def test_unsupported_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported provider"):
            llm_client.create_llm_client("unknown")


if __name__ == "__main__":
    unittest.main()
