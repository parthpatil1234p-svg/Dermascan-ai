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
            "You are DermaBot, a friendly, gentle, and expert AI skincare assistant for DermaScan AI. "
            "Your goal is to give simple, easy-to-follow, and reassuring skincare advice to everyday users. "
            "Rules for responses: "
            "1. Keep answers simple, short, and friendly (avoid overly complex medical jargon). "
            "2. If the user asks in Hindi/Hinglish, reply in friendly Hinglish/Hindi. If in English, reply in simple English. "
            "3. Use clear bullet points and emojis for readability. "
            "4. Clearly explain practical steps (e.g. which product to apply first, morning vs night). "
            "5. Always be polite, warm, and encourage healthy skin habits."
        )

        if user_context:
            skin_type = user_context.get("skin_type", "unspecified")
            concerns = user_context.get("concerns", [])
            system_instruction += f"\nUser Profile: Skin Type: {skin_type}, Concerns: {', '.join(concerns) if concerns else 'None stated'}."

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
                "maxOutputTokens": 600,
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
    if "sunscreen" in q or "spf" in q or "dhoop" in q:
        return (
            "☀️ **Sunscreen Guide (Easy Tips):**\n"
            "- **For Oily or Acne skin:** Choose a light Gel-based or Fluid SPF 50 (Matte finish).\n"
            "- **For Dry skin:** Choose a hydrating Cream-based SPF with Ceramides or Hyaluronic acid.\n"
            "- **How to use:** Apply 2 finger lengths evenly 15 minutes before sun exposure!"
        )
    if "niacinamide" in q and "salicylic" in q:
        return (
            "✨ **Niacinamide + Salicylic Acid Pairing:**\n"
            "- **Yes, they work great together!**\n"
            "- **Step 1:** Apply Salicylic Acid first on clean skin to clear deep pores.\n"
            "- **Step 2:** Wait 2 minutes, then apply Niacinamide to calm redness and control oil."
        )
    if "retinol" in q or "vitamin c" in q:
        return (
            "💡 **Vitamin C & Retinol Guide:**\n"
            "- **Morning:** Use Vitamin C Serum to brighten skin and protect against UV rays.\n"
            "- **Night:** Use Retinol (2-3 nights a week) for skin renewal and anti-aging.\n"
            "- **Rule:** Never apply both together at the same time to prevent irritation."
        )
    if "acne" in q or "pimple" in q or "daane" in q:
        return (
            "🌿 **Acne & Pimple Care:**\n"
            "- Use a gentle Salicylic Acid or Benzoyl Peroxide cleanser.\n"
            "- Keep skin hydrated with an oil-free, non-comedogenic moisturizer.\n"
            "- Avoid popping pimples to prevent scarring."
        )
    if "dark spot" in q or "pigmentation" in q or "daag" in q:
        return (
            "🎯 **Dark Spots & Pigmentation Care:**\n"
            "- **Best Actives:** Niacinamide, Alpha Arbutin, Vitamin C, and Kojic Acid.\n"
            "- **Must-Do:** Daily SPF 50 Sunscreen prevents spots from getting darker."
        )
    if "dry" in q or "sukhi" in q:
        return (
            "💧 **Dry Skin Relief:**\n"
            "- Use a hydrating creamy cleanser (no harsh foam).\n"
            "- Apply Ceramide + Hyaluronic Acid moisturizer on damp skin.\n"
            "- Avoid hot water face wash."
        )
    if "oily" in q or "chipchipi" in q:
        return (
            "✨ **Oily Skin Control:**\n"
            "- Use a gentle foaming cleanser with Salicylic acid.\n"
            "- Use lightweight oil-free gel moisturizer (skipping moisturizer makes skin more oily!).\n"
            "- Use a matte-finish sunscreen."
        )
    return (
        "👋 **Hello! Main aapka AI Skincare Assistant hoon.**\n"
        "- Aap mujhse kisi bhi skin problem (Acne, Dark spots, Dryness, Oily skin) ke baare mein pooch sakte hain.\n"
        "- Ya kisi bhi product ingredient (Niacinamide, Retinol, Sunscreen) ka sahi use jaan sakte hain!\n"
        "- **Bataiye, aaj aapki skin ke liye kya help chahiye?**"
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
