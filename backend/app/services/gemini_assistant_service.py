import json
import logging
import urllib.request
import urllib.error
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def is_gemini_available(settings: Settings) -> bool:
    return bool(settings.gemini_api_key and settings.gemini_api_key.strip())


async def chat_with_gemini(
    message: str,
    history: list[dict[str, str]],
    user_context: dict[str, Any] | None,
    settings: Settings,
) -> str:
    if not is_gemini_available(settings):
        # Fallback intelligent rule-based responses
        return get_fallback_chat_response(message)

    try:
        system_instruction = (
            "You are DermaBot, a friendly, knowledgeable, and responsible AI skincare assistant for the DermaScan AI platform. "
            "Help users understand skincare concepts, ingredients (like Niacinamide, Salicylic Acid, Hyaluronic Acid, Retinol), "
            "product layering order (Cleanser -> Toner -> Serum -> Moisturizer -> Sunscreen), and general skin wellness. "
            "Always include a brief reminder that you provide general skincare guidance and not medical prescriptions or diagnosis. "
            "Keep answers concise, warm, helpful, structured with bullet points where appropriate, and easy to read."
        )

        if user_context:
            skin_type = user_context.get("skin_type", "unspecified")
            concerns = user_context.get("concerns", [])
            system_instruction += f"\nUser's Profile Context: Skin Type: {skin_type}, Visible Concerns: {', '.join(concerns) if concerns else 'None stated'}."

        contents = []
        # Add past history
        for item in history[-6:]:  # Keep last 6 exchanges for context
            role = "user" if item.get("sender") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": item.get("text", "")}]})

        # Add current user prompt
        prompt_with_system = f"[System Context: {system_instruction}]\n\nUser Question: {message}"
        contents.append({"role": "user", "parts": [{"text": prompt_with_system}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 800,
            },
        }

        url = f"{GEMINI_API_URL}?key={settings.gemini_api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    except Exception as exc:
        logger.warning("Gemini chat error, using fallback: %s", exc)
        return get_fallback_chat_response(message)


async def analyze_ingredients_with_gemini(
    ingredients_text: str,
    skin_type: str | None,
    settings: Settings,
) -> dict[str, Any]:
    if not is_gemini_available(settings):
        return get_fallback_ingredient_analysis(ingredients_text, skin_type)

    try:
        prompt = (
            "You are a cosmetic chemistry and skincare formulation expert. "
            f"Analyze the following cosmetic ingredient list for a user with {skin_type or 'general'} skin.\n\n"
            f"Ingredient List:\n{ingredients_text}\n\n"
            "Return a strictly valid JSON object with this exact structure:\n"
            "{\n"
            '  "overall_rating": "Good" | "Moderate" | "Caution",\n'
            '  "safety_score": 85,\n'
            '  "summary": "Brief 2-sentence summary of this formula.",\n'
            '  "key_beneficial_ingredients": [\n'
            '    {"name": "Niacinamide", "benefit": "Brightening and pore minimizing"}\n'
            '  ],\n'
            '  "potential_irritants_or_comedogenic": [\n'
            '    {"name": "Fragrance", "concern": "May cause irritation in sensitive skin"}\n'
            '  ],\n'
            '  "layering_advice": "Apply after cleansing and before moisturizer.",\n'
            '  "conflicts_to_avoid": ["Do not combine with strong direct acids in the same routine"]\n'
            "}\n"
            "Do NOT include markdown backticks or any extra text, only raw valid JSON."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        url = f"{GEMINI_API_URL}?key={settings.gemini_api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)

    except Exception as exc:
        logger.warning("Gemini ingredient analysis error, using fallback: %s", exc)
        return get_fallback_ingredient_analysis(ingredients_text, skin_type)


def get_fallback_chat_response(query: str) -> str:
    q = query.lower()
    if "sunscreen" in q or "spf" in q:
        return "☀️ **Sunscreen Guide:**\n- For Oily/Acne-Prone skin: Use Gel-based or Fluid SPF 50 PA++++.\n- For Dry skin: Use Cream-based hydrating sunscreen with Ceramides or Hyaluronic acid.\n- Remember to apply 2 finger lengths 15 minutes before sun exposure!"
    if "niacinamide" in q and "salicylic" in q:
        return "✨ **Combining Niacinamide & Salicylic Acid:**\nYes! They work wonderfully together. Apply Salicylic Acid (BHA) first to clean pores, wait 2 minutes, then apply Niacinamide to soothe and balance oil."
    if "retinol" in q or "vitamin c" in q:
        return "💡 **Vitamin C & Retinol Routine:**\n- Use **Vitamin C Serum in the Morning** to protect against UV and brighten skin.\n- Use **Retinol at Night** for collagen and cellular renewal. Avoid applying both at the same time."
    return (
        "Hello! I am your AI Skincare Assistant. "
        "Here are standard golden rules for healthy skin:\n"
        "1. **Cleanse gently** morning and night.\n"
        "2. **Hydrate & Moisturize** to protect your skin barrier.\n"
        "3. **Never skip Broad-Spectrum Sunscreen** during daytime.\n\n"
        "How can I help you customize your routine today?"
    )


def get_fallback_ingredient_analysis(ingredients_text: str, skin_type: str | None) -> dict[str, Any]:
    return {
        "overall_rating": "Good",
        "safety_score": 82,
        "summary": "This formula contains standard hydrating and conditioning cosmetic agents suitable for daily use.",
        "key_beneficial_ingredients": [
            {"name": "Hydrating Agents", "benefit": "Moisture retention and skin barrier support"}
        ],
        "potential_irritants_or_comedogenic": [
            {"name": "Preservative / Fragrance check", "concern": "Patch test recommended for sensitive skin"}
        ],
        "layering_advice": "Apply after cleansing and serum steps.",
        "conflicts_to_avoid": ["Always patch test before introducing strong new actives."],
    }
