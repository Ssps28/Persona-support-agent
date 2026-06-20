"""
app.py
Streamlit chat UI for the Persona-Adaptive Customer Support Agent.

Run locally with:  streamlit run app.py
"""

import json
import streamlit as st

from src import config
from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response

st.set_page_config(
    page_title="CloudSuite Support Agent",
    page_icon="🎧",
    layout="wide",
)

PERSONA_BADGE = {
    "Technical Expert": "🛠️ Technical Expert",
    "Frustrated User": "😤 Frustrated User",
    "Business Executive": "📊 Business Executive",
}


# ---------- Cached resources ----------

@st.cache_resource(show_spinner=False)
def get_pipeline():
    return LocalRAGPipeline()


def ensure_index_built(pipeline: LocalRAGPipeline):
    if pipeline.is_indexed():
        return
    with st.spinner("Indexing knowledge base for the first time — this happens once..."):
        progress_bar = st.progress(0.0, text="Starting ingestion...")

        def progress_callback(current, total, filename):
            progress_bar.progress(current / total, text=f"Indexed {filename} ({current}/{total})")

        count = pipeline.ingest_directory(progress_callback=progress_callback)
        progress_bar.empty()
    st.toast(f"Indexed {count} documents into the knowledge base.", icon="✅")


# ---------- Session state ----------

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {role, content, meta}
if "consecutive_frustration" not in st.session_state:
    st.session_state.consecutive_frustration = 0
if "attempted_steps" not in st.session_state:
    st.session_state.attempted_steps = []


# ---------- Sidebar ----------

with st.sidebar:
    st.title("🎧 CloudSuite Support")
    st.caption("Persona-Adaptive Customer Support Agent")

    st.markdown("---")
    st.subheader("How it works")
    st.markdown(
        "1. Your message is classified into a **persona**\n"
        "2. Relevant docs are retrieved from the **knowledge base**\n"
        "3. A response is generated, **adapted to your persona**\n"
        "4. Sensitive or low-confidence issues are **escalated** to a human"
    )

    st.markdown("---")
    st.subheader("Try an example")
    examples = [
        "Where is the guide to clear cookies? It's been an hour and nothing is loading on your interface!",
        "What are the header parameter requirements for your bearer token auth implementation?",
        "Our operational uptime is decreasing. We need a timeline of when billing disputes are resolved.",
        "I'm experiencing an issue with your database integration that's causing internal errors.",
        "My billing statement has unexpected duplicate charges. I demand an immediate refund!",
    ]
    for ex in examples:
        if st.button(ex[:60] + ("..." if len(ex) > 60 else ""), key=ex, use_container_width=True):
            st.session_state["pending_input"] = ex

    st.markdown("---")
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.consecutive_frustration = 0
        st.session_state.attempted_steps = []
        st.rerun()

    with st.expander("⚙️ Escalation thresholds (config)"):
        st.write(f"Retrieval confidence threshold: `{config.RETRIEVAL_CONFIDENCE_THRESHOLD}`")
        st.write(f"Frustration turn limit: `{config.MAX_CONSECUTIVE_FRUSTRATION_TURNS}`")
        st.write(f"Sensitive keywords tracked: `{len(config.SENSITIVE_KEYWORDS)}`")


# ---------- Main area ----------

st.title("CloudSuite Support Agent")
st.caption("Ask a question the way you normally would — the agent adapts its tone to you.")

if not config.GEMINI_API_KEY:
    st.error(
        "No GEMINI_API_KEY found. Add it to a `.env` file locally, or to "
        "Streamlit Cloud's app secrets when deployed."
    )
    st.stop()

pipeline = get_pipeline()
ensure_index_built(pipeline)

# Render past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        meta = msg.get("meta")
        if meta:
            cols = st.columns(3)
            cols[0].markdown(f"**Persona:** {PERSONA_BADGE.get(meta['persona'], meta['persona'])}")
            cols[1].markdown(f"**Escalated:** {'🚨 Yes' if meta['escalated'] else '✅ No'}")
            cols[2].markdown(f"**Top score:** `{meta.get('best_score', 0):.2f}`")

            if meta.get("sources"):
                with st.expander("📚 Retrieved sources"):
                    for s in meta["sources"]:
                        st.markdown(f"- `{s['source']}` (chunk {s['chunk_index']}, score `{s['score']}`)")
                        st.caption(s["text"][:250] + "...")

            if meta.get("handoff_summary"):
                with st.expander("🚨 Human handoff summary (JSON)"):
                    st.json(meta["handoff_summary"])

# Chat input (also handles example button clicks)
pending = st.session_state.pop("pending_input", None)
user_input = st.chat_input("Type your support question...")
final_input = pending or user_input

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input, "meta": None})
    with st.chat_message("user"):
        st.markdown(final_input)

    with st.chat_message("assistant"):
        with st.spinner("Classifying persona..."):
            classification = classify_customer_persona(final_input)
            persona = classification["persona"]

        with st.spinner("Searching knowledge base..."):
            context_chunks = pipeline.retrieve_context(final_input)

        # Track consecutive frustration across turns for the escalation rule
        if persona == "Frustrated User":
            st.session_state.consecutive_frustration += 1
        else:
            st.session_state.consecutive_frustration = 0

        with st.spinner("Generating response..."):
            result = generate_adaptive_response(
                user_query=final_input,
                persona=persona,
                context_chunks=context_chunks,
                conversation_history=st.session_state.messages,
                consecutive_frustration_turns=st.session_state.consecutive_frustration,
                attempted_steps=st.session_state.attempted_steps,
            )

        st.markdown(result["response"])

        best_score = max([c["score"] for c in context_chunks]) if context_chunks else 0.0
        cols = st.columns(3)
        cols[0].markdown(f"**Persona:** {PERSONA_BADGE.get(persona, persona)}")
        cols[1].markdown(f"**Escalated:** {'🚨 Yes' if result['escalated'] else '✅ No'}")
        cols[2].markdown(f"**Top score:** `{best_score:.2f}`")

        if context_chunks:
            with st.expander("📚 Retrieved sources"):
                for s in context_chunks:
                    st.markdown(f"- `{s['source']}` (chunk {s['chunk_index']}, score `{s['score']}`)")
                    st.caption(s["text"][:250] + "...")

        if result["handoff_summary"]:
            with st.expander("🚨 Human handoff summary (JSON)", expanded=True):
                st.json(result["handoff_summary"])
            st.session_state.attempted_steps = []  # reset after handoff
        else:
            st.session_state.attempted_steps.append(final_input[:80])

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["response"],
        "meta": {
            "persona": persona,
            "escalated": result["escalated"],
            "best_score": best_score,
            "sources": context_chunks,
            "handoff_summary": result["handoff_summary"],
        },
    })
