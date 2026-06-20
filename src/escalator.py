"""
escalator.py
Decides whether a conversation should be escalated to a human agent, and
builds the structured handoff JSON summary when it is.
"""

import json
import datetime
from src import config


def contains_sensitive_topic(text: str) -> bool:
    """Check the user's message for account-sensitive keywords (billing, legal, etc.)."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in config.SENSITIVE_KEYWORDS)


def should_escalate(
    user_query: str,
    context_chunks: list,
    persona: str,
    consecutive_frustration_turns: int = 0,
) -> dict:
    """
    Evaluates all escalation triggers and returns a dict describing whether to
    escalate and why. Keeping this separate from response generation means the
    UI can show *why* an escalation happened, which the assignment requires.
    """
    reasons = []

    # Trigger 1: Low retrieval confidence
    best_score = max([c["score"] for c in context_chunks]) if context_chunks else 0.0
    if not context_chunks or best_score < config.RETRIEVAL_CONFIDENCE_THRESHOLD:
        reasons.append(
            f"Low retrieval confidence (best score {best_score:.2f} is below "
            f"threshold {config.RETRIEVAL_CONFIDENCE_THRESHOLD})"
        )

    # Trigger 2: Sensitive topic keywords (billing, legal, account deletion, etc.)
    if contains_sensitive_topic(user_query):
        reasons.append("Message touches a billing/legal/account-sensitive topic")

    # Trigger 3: Repeated frustration across turns
    if consecutive_frustration_turns >= config.MAX_CONSECUTIVE_FRUSTRATION_TURNS:
        reasons.append(
            f"User has shown frustration for {consecutive_frustration_turns} "
            "consecutive turns without resolution"
        )

    return {
        "escalate": len(reasons) > 0,
        "reasons": reasons,
        "best_retrieval_score": best_score,
    }


def generate_handoff_summary(
    user_query: str,
    persona: str,
    context_chunks: list,
    escalation_result: dict,
    conversation_history: list = None,
    attempted_steps: list = None,
) -> dict:
    """
    Compiles a structured handoff summary for a human support agent.
    Returns a dict (caller can json.dumps it for display).
    """
    conversation_history = conversation_history or []
    attempted_steps = attempted_steps or []

    handoff = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "persona": persona,
        "issue_summary": user_query[:200] + ("..." if len(user_query) > 200 else ""),
        "escalation_reasons": escalation_result["reasons"],
        "retrieved_sources": list({c["source"] for c in context_chunks}) if context_chunks else [],
        "best_retrieval_confidence": escalation_result["best_retrieval_score"],
        "conversation_turn_count": len(conversation_history),
        "attempted_steps": attempted_steps,
        "recommended_action": _recommend_action(persona, escalation_result["reasons"]),
    }
    return handoff


def _recommend_action(persona: str, reasons: list) -> str:
    """Simple rule-based recommendation text based on why escalation triggered."""
    reasons_text = " ".join(reasons).lower()

    if "billing" in reasons_text or "sensitive" in reasons_text:
        return "Route to billing/account specialist for manual review; verify identity before taking action."
    if "low retrieval" in reasons_text:
        return "No confident match in knowledge base — review with a human agent and consider adding a new KB article if this is a recurring query."
    if "frustration" in reasons_text:
        return "Prioritize this conversation; user has been unresolved across multiple turns. Consider a direct call instead of further async messages."
    return "Review conversation manually and respond directly to the customer."


if __name__ == "__main__":
    sample_chunks = [{"text": "...", "source": "billing_policy.txt", "score": 0.3}]
    result = should_escalate("My billing statement has duplicate charges, I demand a refund!", sample_chunks, "Frustrated User")
    print(json.dumps(result, indent=2))
    handoff = generate_handoff_summary(
        "My billing statement has duplicate charges, I demand a refund!",
        "Frustrated User",
        sample_chunks,
        result,
    )
    print(json.dumps(handoff, indent=2))
