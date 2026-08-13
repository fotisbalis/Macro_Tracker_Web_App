import json
import os

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    from ..schemas import MacroResult
    from .ai_service import AIService, AIServiceError
except ImportError:
    from schemas import MacroResult
    from services.ai_service import AIService, AIServiceError


DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.5-flash"
SYSTEM_PROMPT = """You estimate the nutritional macros of a food serving.
Return only one valid JSON object with exactly these numeric fields:
calories, protein, carbs, fat.
Calories are kcal. Protein, carbs, and fat are grams.
Use the supplied food name and quantity in grams. Estimate the full serving, not 100g.
All values must be non-negative numbers. Do not include markdown or commentary.
This is an estimate, so choose a reasonable single value for each field."""


class QwenMacroPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    calories: float = Field(ge=0, le=50000)
    protein: float = Field(ge=0, le=5000)
    carbs: float = Field(ge=0, le=5000)
    fat: float = Field(ge=0, le=5000)


class QwenAIService(AIService):
    def __init__(self, client=None):
        self.model = os.getenv("QWEN_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        self._client = client

        if self._client is None:
            api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
            if api_key:
                try:
                    timeout = float(os.getenv("QWEN_TIMEOUT_SECONDS", "30"))
                except ValueError:
                    timeout = 30.0
                self._client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=os.getenv("QWEN_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
                    timeout=timeout,
                    max_retries=1,
                )

    async def analyze_food(self, food_name: str, quantity: float) -> MacroResult:
        if self._client is None:
            raise AIServiceError(
                "Qwen is selected but DASHSCOPE_API_KEY is missing from the .env file."
            )

        try:
            completion = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": "Return the macro estimate as JSON for this serving: "
                        + json.dumps({"food_name": food_name, "quantity_grams": quantity}),
                    },
                ],
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False},
                temperature=0.1,
                max_tokens=250,
            )
            content = completion.choices[0].message.content
            if not content:
                raise AIServiceError("Qwen returned an empty response.")

            payload = QwenMacroPayload.model_validate(json.loads(content))
            return MacroResult(
                food_name=food_name,
                quantity=quantity,
                unit="g",
                calories=payload.calories,
                protein=payload.protein,
                carbs=payload.carbs,
                fat=payload.fat,
                source=f"qwen:{self.model}"[:40],
            )
        except AIServiceError:
            raise
        except (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            json.JSONDecodeError,
            AttributeError,
            IndexError,
            KeyError,
            TypeError,
            ValueError,
            ValidationError,
        ) as exc:
            raise AIServiceError("Qwen could not return a valid macro estimate.") from exc
