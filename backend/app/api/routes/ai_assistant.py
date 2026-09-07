from typing import Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.services.gemini_assistant_service import (
    chat_with_gemini,
    analyze_ingredients_with_gemini,
)

router = APIRouter(prefix="/ai", tags=["ai assistant"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[dict[str, str]] = Field(default_factory=list)
    user_context: dict[str, Any] | None = None


class ChatMessageResponse(BaseModel):
    response: str
    status: str = "success"


class IngredientCheckRequest(BaseModel):
    ingredients_text: str = Field(..., min_length=2, max_length=5000)
    skin_type: str | None = None


class IngredientCheckResponse(BaseModel):
    analysis: dict[str, Any]
    status: str = "success"


@router.post("/chat", response_model=ChatMessageResponse)
async def handle_ai_chat(
    payload: ChatMessageRequest,
    settings: Settings = Depends(get_settings),
) -> ChatMessageResponse:
    try:
        reply = await chat_with_gemini(
            message=payload.message,
            history=payload.history,
            user_context=payload.user_context,
            settings=settings,
        )
        return ChatMessageResponse(response=reply)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI chat error: {str(exc)}") from exc


@router.post("/ingredient-check", response_model=IngredientCheckResponse)
async def handle_ingredient_check(
    payload: IngredientCheckRequest,
    settings: Settings = Depends(get_settings),
) -> IngredientCheckResponse:
    try:
        analysis = await analyze_ingredients_with_gemini(
            ingredients_text=payload.ingredients_text,
            skin_type=payload.skin_type,
            settings=settings,
        )
        return IngredientCheckResponse(analysis=analysis)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingredient analysis error: {str(exc)}") from exc
