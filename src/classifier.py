"""
classifier.py
Detects which of three customer personas (Technical Expert, Frustrated User,
Business Executive) a given message belongs to, using Gemini with a strict
JSON schema so the output is always parseable.
"""

import json
from google import genai
from google.genai import types

from src import config

SYSTEM_INSTRUCTION = (
    "You are an advanced classification engine for a customer support system. "
    "Your task is to analyze the sentiment, vocabulary, and tone of an incoming "
    "support message and classify it into exactly one of three customer personas:\n\n"
    "1. 'Technical Expert': Uses technical jargon, asks about APIs, error codes, "
    "configurations, logs, or integrations. Wants precise, detailed answers.\n"
    "2. 'Frustrated User': Uses emotional language, exclamation marks, words like "
    "'nothing works', 'still broken', urgency, or repeated complaints.\n"
    "3. 'Business Executive': Focuses on business impact, operational risk, ROI, "
    "timelines, SLAs, or resolution dates. Prefers brevity over technical detail.\n\n"
    "If a message could plausibly fit more than one persona, pick the one whose "
    "signal is strongest in the actual wording used. Provide your evaluation "
    "strictly in the requested JSON structure with a brief reasoning."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "persona": {
            "type": "STRING",
            "enum": config.PERSONAS,
        },
        "confidence": {"type": "NUMBER"},
        "reasoning": {"type": "STRING"},
    },
    "required": ["persona", "confidence", "reasoning"],
}


def classify_customer_persona(user_message: str) -> dict:
    """
    Classifies a support message into one of the three target personas.
    Returns a dict: {"persona": str, "confidence": float, "reasoning": str}
    Falls back to a safe default if the API call fails for any reason, so the
    rest of the pipeline never crashes on a classification hiccup.
    """
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)

        response = client.models.generate_content(
            model=config.GENERATION_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                temperature=0.1,
            ),
        )
        result = json.loads(response.text)

        # Defensive normalization in case the model returns an unexpected persona string
        if result.get("persona") not in config.PERSONAS:
            result["persona"] = "Business Executive"
        return result

    except Exception as e:
        return {
            "persona": "Business Executive",
            "confidence": 0.0,
            "reasoning": f"Classification failed, defaulted to a safe persona. Error: {e}",
        }


if __name__ == "__main__":
    test_messages = [
        "Where is the guide to clear cookies? It's been an hour and nothing is loading!",
        "What are the header parameter requirements for your bearer token auth implementation?",
        "Our operational uptime is decreasing. We need a timeline of when billing disputes are resolved.",
    ]
    for msg in test_messages:
        print(f"\nInput: {msg}")
        print(json.dumps(classify_customer_persona(msg), indent=2))
