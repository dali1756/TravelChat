from collections.abc import Iterator

_STUB_REPLY = (
    "（這是測試用的 stub 回應，還沒有設定 GEMINI_API_KEY）\n"
    "我可以協助你規劃旅遊行程！這裡先示範串流回應：\n"
    "第一天：抵達當地後安排市區輕鬆行程與在地美食。\n"
    "第二天：前往主要景點，搭配幾個停留點看看自然景觀。\n"
    "第三天：購物、伴手禮後回程。\n"
    "設定 GEMINI_API_KEY 後即可改用真實 Gemini 回應。"
)


class StubProvider:
    """
    未設定 GEMINI_API_KEY 時使用的假 provider，回傳固定回應並切段模擬串流。
    """

    def stream(self, messages: list[dict], system_prompt: str) -> Iterator[str]:
        for line in _STUB_REPLY.splitlines(keepends=True):
            yield line
