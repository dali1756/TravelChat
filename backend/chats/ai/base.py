from collections.abc import Iterator
from typing import Protocol


class AIProvider(Protocol):
    """
    AI 串流回應 provider 介面。
    實作 MUST 提供同步產生器 `stream`，逐段 yield 回應文字片段，
    讓 consumer 不需知道底層是 stub 或真實 Gemini。
    """

    def stream(self, messages: list[dict], system_prompt: str) -> Iterator[str]:
        """
        依對話歷史與 system prompt 逐段 yield 回應文字。
        messages: [{"role": "user"|"model", "content": str}, ...]，依時間排序。
        """
        pass
