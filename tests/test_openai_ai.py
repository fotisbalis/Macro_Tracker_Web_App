import asyncio
import json
from types import SimpleNamespace

import pytest

from backend.services.ai_service import AIServiceError
from backend.services.openai_ai import OpenAIAIService


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


def test_openai_returns_validated_macro_result():
    client = FakeClient(json.dumps({
        "quantity_grams": 250,
        "calories": 412.5,
        "protein": 77.5,
        "carbs": 0,
        "fat": 9,
    }))
    service = OpenAIAIService(client=client)

    result = asyncio.run(service.analyze_food("Chicken breast", 250))

    assert result.food_name == "Chicken breast"
    assert result.quantity == 250
    assert result.unit == "g"
    assert result.calories == 412.5
    assert result.protein == 77.5
    assert result.carbs == 0
    assert result.fat == 9
    assert result.source.startswith("openai:")
    response_format = client.completions.call["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True


def test_openai_uses_inferred_quantity_when_none_is_supplied():
    client = FakeClient(json.dumps({
        "quantity_grams": 100,
        "calories": 156,
        "protein": 12.6,
        "carbs": 1.2,
        "fat": 10.6,
    }))
    service = OpenAIAIService(client=client)

    result = asyncio.run(service.analyze_food("two boiled eggs", None))

    assert result.quantity == 100
    prompt = client.completions.call["messages"][1]["content"]
    assert "quantity_grams" not in prompt


@pytest.mark.parametrize("content", [
    "not JSON",
    json.dumps({"quantity_grams": 100, "calories": -1, "protein": 20, "carbs": 10, "fat": 5}),
    json.dumps({
        "quantity_grams": 100,
        "calories": 300,
        "protein": 20,
        "carbs": 10,
        "fat": 5,
        "explanation": "extra output",
    }),
])
def test_openai_rejects_invalid_or_unexpected_output(content):
    service = OpenAIAIService(client=FakeClient(content))

    with pytest.raises(AIServiceError):
        asyncio.run(service.analyze_food("Test food", 100))


def test_openai_reports_missing_key_without_calling_provider():
    service = OpenAIAIService(api_key_loader=lambda: None)

    with pytest.raises(AIServiceError, match="AI is inactive"):
        asyncio.run(service.analyze_food("Test food", 100))
