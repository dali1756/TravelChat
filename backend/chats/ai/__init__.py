from django.conf import settings

from chats.ai.base import AIProvider
from chats.ai.gemini import GeminiProvider
from chats.ai.stub import StubProvider

__all__ = ["AIProvider", "GeminiProvider", "StubProvider", "get_provider"]


def get_provider() -> AIProvider:
    """依設定選擇 provider：有 GEMINI_API_KEY 用真實 Gemini，否則用 stub。"""
    if settings.GEMINI_API_KEY:
        return GeminiProvider()
    return StubProvider()
