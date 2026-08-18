import json
import os
from typing import Optional

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    from ..schemas import MacroResult
    from .ai_service import AIInactiveError, AIService, AIServiceError
    from .api_key_store import APIKeyStorageError, load_api_key
except ImportError:
    from schemas import MacroResult
    from services.ai_service import AIInactiveError, AIService, AIServiceError
    from services.api_key_store import APIKeyStorageError, load_api_key


DEFAULT_MODEL = "gpt-5.6-luna"
SYSTEM_PROMPT = """You estimate the nutritional macros of a food serving.
Return an estimate for the full serving, not for 100 grams. If quantity_grams is supplied,
use it exactly. If it is not supplied, infer a reasonable total serving weight from the food
description (for example, "two boiled eggs") and return that weight as quantity_grams.
Calories are kcal; protein, carbs, and fat are grams. Choose reasonable single values based
on common food nutrition data. All values must be non-negative. Do not provide medical
advice, explanations, or markdown."""


class OpenAIMacroPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    quantity_grams: float = Field(gt=0, le=5000)
    calories: float = Field(ge=0, le=50000)
    protein: float = Field(ge=0, le=5000)
    carbs: float = Field(ge=0, le=5000)
    fat: float = Field(ge=0, le=5000)


class OpenAIAIService(AIService):
    def __init__(self, client=None, api_key_loader=load_api_key):
        self.model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        self._client = client
        self._api_key_loader = api_key_loader

    def _create_client(self):
        if self._client is not None:
            return self._client
        try:
            api_key = self._api_key_loader()
        except APIKeyStorageError as exc:
            raise AIServiceError("The protected OpenAI API key could not be accessed.") from exc
        if not api_key:
            raise AIInactiveError(
                "AI is inactive. Add your OpenAI API key in AI settings."
            )
        try:
            timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))
        except ValueError:
            timeout = 30.0
        return AsyncOpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=1,
        )

    async def analyze_food(self, food_name: str, quantity: Optional[float]) -> MacroResult:
        try:
            client = self._create_client()
            serving = {"food_name": food_name}
            if quantity is not None:
                serving["quantity_grams"] = quantity

            completion = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": "Return the macro estimate for this serving: "
                        + json.dumps(serving),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "macro_estimate",
                        "strict": True,
                        "schema": OpenAIMacroPayload.model_json_schema(),
                    },
                },
            )
            content = completion.choices[0].message.content
            if not content:
                raise AIServiceError("OpenAI returned an empty response.")

            payload = OpenAIMacroPayload.model_validate(json.loads(content))
            return MacroResult(
                food_name=food_name,
                quantity=quantity if quantity is not None else payload.quantity_grams,
                unit="g",
                calories=payload.calories,
                protein=payload.protein,
                carbs=payload.carbs,
                fat=payload.fat,
                source=f"openai:{self.model}"[:40],
            )
        except (AIInactiveError, AIServiceError):
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
            raise AIServiceError("OpenAI could not return a valid macro estimate.") from exc
