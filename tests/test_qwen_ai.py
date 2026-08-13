import asyncio
import json
from types import SimpleNamespace

import pytest

from backend.services.ai_service import AIServiceError
from backend.services.qwen_ai import QwenAIService


class FakeCompletions:
    def __init__(self, content):
        self.content = content
        self.call = None

    async def create(self, **kwargs):
        self.call = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeClient:
    def __init__(self, content):
        self.completions = FakeCompletions(content)
        self.chat = SimpleNamespace(completions=self.completions)


def test_qwen_returns_validated_macro_result():
    client = FakeClient(json.dumps({
        "calories": 412.5,
        "protein": 77.5,
        "carbs": 0,
        "fat": 9,
    }))
    service = QwenAIService(client=client)

    result = asyncio.run(service.analyze_food("Chicken breast", 250))

    assert result.food_name == "Chicken breast"
    assert result.quantity == 250
    assert result.unit == "g"
    assert result.calories == 412.5
    assert result.protein == 77.5
    assert result.carbs == 0
    assert result.fat == 9
    assert result.source.startswith("qwen:")
    assert client.completions.call["extra_body"] == {"enable_thinking": False}
    assert client.completions.call["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize("content", [
    "not JSON",
    json.dumps({"calories": -1, "protein": 20, "carbs": 10, "fat": 5}),
    json.dumps({
        "calories": 300,
        "protein": 20,
        "carbs": 10,
        "fat": 5,
        "explanation": "extra output",
    }),
])
def test_qwen_rejects_invalid_or_unexpected_output(content):
    service = QwenAIService(client=FakeClient(content))

    with pytest.raises(AIServiceError):
        asyncio.run(service.analyze_food("Test food", 100))


def test_qwen_reports_missing_key_without_calling_provider(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    service = QwenAIService()

    with pytest.raises(AIServiceError, match="DASHSCOPE_API_KEY"):
        asyncio.run(service.analyze_food("Test food", 100))
