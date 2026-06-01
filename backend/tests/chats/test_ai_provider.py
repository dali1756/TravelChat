from chats.ai import get_provider
from chats.ai.gemini import GeminiProvider
from chats.ai.stub import StubProvider


class TestProviderFactory:
    def test_returns_stub_when_no_api_key(self, settings):
        settings.GEMINI_API_KEY = None
        provider = get_provider()
        assert isinstance(provider, StubProvider)

    def test_returns_gemini_when_api_key_set(self, settings):
        settings.GEMINI_API_KEY = "fake-key-for-test"
        provider = get_provider()
        assert isinstance(provider, GeminiProvider)


class TestStubProvider:
    def test_stream_yields_text_chunks(self):
        provider = StubProvider()
        messages = [{"role": "user", "content": "幫我規劃東京三天行程"}]
        chunks = list(provider.stream(messages, system_prompt="你是旅遊小幫手"))
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)

    def test_stream_full_text_non_empty(self):
        provider = StubProvider()
        messages = [{"role": "user", "content": "hi"}]
        full = "".join(provider.stream(messages, system_prompt="x"))
        assert full.strip() != ""
