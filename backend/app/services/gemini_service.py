import base64
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def is_gemini_configured(settings: Settings) -> bool:
    return bool(settings.gemini_api_key and settings.gemini_api_key.strip())


async def analyze_skin_with_gemini(
    image_path: Path,
    questionnaire_data: dict[str, Any],
    settings: Settings,
) -> dict[str, Any] | None:
    if not is_gemini_configured(settings):
        return None

    try:
        with open(image_path, "rb") as img_file:
            image_b64 = base64.b64encode(img_file.read()).decode("utf-8")

        prompt = (
            "You are a professional, responsible skincare AI assistant. "
            "Analyze the provided facial skin image and user background information to provide non-diagnostic skincare guidance.\n"
            f"User Questionnaire Data: {json.dumps(questionnaire_data)}\n\n"
            "Return a strictly valid JSON object with the following structure:\n"
            "{\n"
            '  "skin_type": "oily" | "dry" | "combination" | "normal",\n'
            '  "confidence": 0.85,\n'
            '  "visible_observations": ["list", "of", "observed", "concerns", "like acne, redness, pores, etc."],\n'
            '  "concerns_analysis": {\n'
            '    "acne_level": "none" | "mild" | "moderate" | "severe",\n'
            '    "redness_level": "none" | "mild" | "moderate" | "severe",\n'
            '    "pigmentation": "none" | "mild" | "moderate" | "severe",\n'
            '    "skin_texture": "smooth" | "rough" | "uneven"\n'
            "  },\n"
            '  "summary": "Brief 2-3 sentence explanation of skin observations."\n'
            "}\n"
            "Do NOT include markdown backticks or any extra text, only raw valid JSON."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_b64,
                            }
                        },
                    ]
                }
            ],
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
        logger.warning("Gemini AI skin analysis fallback: %s", exc)
        return None
