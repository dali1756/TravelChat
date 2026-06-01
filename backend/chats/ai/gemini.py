from collections.abc import Iterator

from django.conf import settings


class GeminiProvider:
    """
    以 google-genai streaming API 取得真實 Gemini 回應。
    client 採 lazy 建立（首次 stream 時才初始化），避免 import 階段就要求 key。
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or settings.GEMINI_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def stream(self, messages: list[dict], system_prompt: str) -> Iterator[str]:
        from google.genai import types

        client = self._get_client()
        contents = [{"role": m["role"], "parts": [{"text": m["content"]}]} for m in messages]
        response = client.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        for chunk in response:
            text = getattr(chunk, "text", None)
            if text:
                yield text
