"""
generator.py
Compiles persona-specific system prompts, calls Gemini grounded strictly on
retrieved context, and orchestrates the escalation check before generating
a response.
"""

from google import genai
from google.genai import types

from src import config
from src.escalator import should_escalate, generate_handoff_summary


PERSONA_INSTRUCTIONS = {
    "Technical Expert": (
        "You are a Senior Systems Engineer speaking to a technically fluent user. "
        "Provide clear root-cause analysis, exact configuration steps, relevant error "
        "codes, and precise terminology. Use code blocks or step lists where helpful. "
        "Do not oversimplify or pad the answer with reassurance — be direct and exact."
    ),
    "Frustrated User": (
        "You are a calm, empathetic Customer Care Specialist. Begin with a brief, "
        "genuine acknowledgment of the user's frustration (one sentence, no more). "
        "Then give simple, numbered action steps in plain language. Avoid jargon. "
        "Keep the tone reassuring and focused on getting them unblocked quickly."
    ),
    "Business Executive": (
        "You are a concise Client Relations Director. Lead with the direct answer, "
        "then note any relevant timeline or business impact. Skip technical "
        "configuration details unless explicitly asked. Keep the entire response "
        "brief — a few sentences, not a full walkthrough."
    ),
}


def generate_adaptive_response(
    user_query: str,
    persona: str,
    context_chunks: list,
    conversation_history: list = None,
    consecutive_frustration_turns: int = 0,
    attempted_steps: list = None,
) -> dict:
    """
    Main orchestration function: checks escalation triggers first, and only
    calls the LLM for a customer-facing response if the conversation should
    NOT be escalated.

    Returns a dict:
      {
        "escalated": bool,
        "response": str,
        "handoff_summary": dict | None,
        "escalation_reasons": list,
      }
    """
    escalation_result = should_escalate(
        user_query, context_chunks, persona, consecutive_frustration_turns
    )

    if escalation_result["escalate"]:
        handoff = generate_handoff_summary(
            user_query,
            persona,
            context_chunks,
            escalation_result,
            conversation_history,
            attempted_steps,
        )
        return {
            "escalated": True,
            "response": (
                "I want to make sure this gets handled correctly, so I'm connecting "
                "you with a human support specialist who can take it from here. "
                "They'll have the full context of this conversation."
            ),
            "handoff_summary": handoff,
            "escalation_reasons": escalation_result["reasons"],
        }

    persona_instructions = PERSONA_INSTRUCTIONS.get(persona, PERSONA_INSTRUCTIONS["Business Executive"])

    context_text = "\n\n".join(
        [f"Source [{c['source']}]: {c['text']}" for c in context_chunks]
    )

    full_system_prompt = (
        f"{persona_instructions}\n\n"
        "CRITICAL RULES:\n"
        "- Base your response ONLY on the FACTUAL CONTEXT DOCUMENTS below.\n"
        "- Do not invent facts, steps, or policies that are not present in the context.\n"
        "- If the context only partially answers the question, answer what you can "
        "and note what isn't covered, rather than guessing.\n\n"
        f"FACTUAL CONTEXT DOCUMENTS:\n{context_text}"
    )

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GENERATION_MODEL,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=full_system_prompt,
                temperature=0.2,
            ),
        )
        response_text = response.text
    except Exception as e:
        response_text = (
            "I ran into an error while generating a response. "
            f"Please try again in a moment. (Details: {e})"
        )

    return {
        "escalated": False,
        "response": response_text,
        "handoff_summary": None,
        "escalation_reasons": [],
    }
