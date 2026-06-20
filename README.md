# CloudSuite Persona-Adaptive Customer Support Agent

An intelligent customer support agent that detects a customer's communication persona, retrieves grounded answers from a knowledge base using RAG, adapts its tone to the detected persona, and escalates to a human agent with a structured handoff summary when appropriate.

**Live demo:** _[add your deployed Streamlit URL here]_
**Demo video:** _[add your screen recording link here]_

---

## 1. Project Overview

This agent simulates a real-world SaaS customer support assistant for a fictional product, **CloudSuite**. When a customer sends a message, the system:

1. Classifies the message into one of three personas — **Technical Expert**, **Frustrated User**, or **Business Executive**
2. Retrieves the most relevant chunks from a knowledge base of 9 support documents (covering passwords, API auth, billing, integrations, permissions, security, exports, uptime, mobile, and notifications) using vector similarity search
3. Generates a response strictly grounded in the retrieved content, written in a tone matched to the detected persona
4. Checks escalation triggers (low retrieval confidence, sensitive topics like billing/legal, or repeated unresolved frustration) and, if triggered, hands off to a human agent with a structured JSON summary instead of guessing

The goal is to demonstrate a practical, human-in-the-loop RAG system rather than a chatbot that always tries to answer everything itself.

---

## 2. Tech Stack

| Component | Choice | Version |
|---|---|---|
| Language | Python | 3.11+ |
| LLM (classification + generation) | Google Gemini | `gemini-2.5-flash` |
| Embeddings | Google Gemini Embeddings | `text-embedding-004` |
| Vector Database | ChromaDB (local, persistent) | `>=0.4.24` |
| Chunking | LangChain Recursive Text Splitter | `>=0.1.0` |
| PDF Parsing | pypdf | `>=3.0.0` |
| UI | Streamlit | `>=1.30.0` |
| Deployment | Streamlit Community Cloud | — |

---

## 3. Architecture

```
                    ┌─────────────────┐
                    │   User Message   │
                    └────────┬─────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │   Persona Classifier     │   (Gemini, structured JSON output)
                │  Technical / Frustrated  │
                │      / Executive         │
                └────────────┬────────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │   RAG Retrieval Layer    │
                │  Query → Embedding →     │
                │  Cosine Similarity →     │
                │   Top-K Chunks (Chroma)  │
                └────────────┬────────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │   Escalation Check       │
                │  - Low confidence?       │
                │  - Sensitive topic?      │
                │  - Repeated frustration? │
                └──────┬───────────┬──────┘
                       │           │
              No escalation   Escalation triggered
                       │           │
                       ▼           ▼
          ┌─────────────────┐  ┌──────────────────────┐
          │ Adaptive Response │  │ Human Handoff JSON    │
          │ (persona-toned,   │  │ (persona, issue,      │
          │  grounded in KB)  │  │  sources, confidence,  │
          └─────────────────┘  │  recommended action)   │
                                └──────────────────────┘
```

Module breakdown:

- `src/classifier.py` — persona detection via Gemini structured output
- `src/rag_pipeline.py` — document ingestion (parsing, chunking, embedding) and retrieval
- `src/generator.py` — persona-specific prompt compilation and grounded response generation
- `src/escalator.py` — escalation rule evaluation and handoff JSON construction
- `src/config.py` — central thresholds and model configuration
- `app.py` — Streamlit chat UI tying everything together

---

## 4. Persona Detection Strategy

**Classification method:** A single Gemini call per incoming message, constrained to a strict JSON schema (`persona`, `confidence`, `reasoning`) via `response_schema`. This avoids brittle regex/keyword matching and avoids free-text parsing errors.

**Prompt design:** The system instruction gives the model explicit, example-backed definitions of each persona (vocabulary cues, intent cues) and asks it to pick the persona whose *signal is strongest in the actual wording*, rather than guessing from topic alone. Temperature is set low (`0.1`) for classification consistency.

**Rules used (heuristics encoded in the prompt, not hardcoded code paths):**
- **Technical Expert** — jargon, APIs, error codes, configs, logs
- **Frustrated User** — emotional language, exclamation marks, urgency, repeated complaints
- **Business Executive** — business impact, ROI, timelines, SLAs, brevity

A safe default (`Business Executive`, the most neutral/conservative tone) is returned if the classification call fails for any reason, so a transient API issue never crashes the pipeline.

---

## 5. RAG Pipeline Design

**Chunking strategy:** `RecursiveCharacterTextSplitter` with `chunk_size=500`, `chunk_overlap=50`. The recursive splitter tries paragraph breaks first, then sentence breaks, then words, so chunks stay topically coherent rather than cutting mid-sentence. The 50-character overlap prevents a step-by-step instruction (e.g., a password reset step) from being split across two chunks and losing context.

**Embedding model:** Gemini `text-embedding-004`, used identically for both document chunks at ingestion time and the user's query at retrieval time, so they live in the same vector space.

**Vector database:** ChromaDB, running locally in persistent mode (`./chroma_db`). Chosen over Pinecone/Qdrant because it requires no external service, no extra API key, and no network dependency — important for a clean one-click deployment on Streamlit Cloud. Metadata stored per chunk: `source` (filename) and `chunk_index`.

**Retrieval strategy:** Top-`k=3` nearest chunks per query, using Chroma's similarity search. Distance is converted to a `0–1` similarity-style score (`1 - distance`) for human-readable confidence display and for the escalation threshold check.

**Ingestion:** Runs once automatically on first app load (`ensure_index_built` in `app.py`), checking `collection.count()` to avoid re-indexing on every restart. A reset method (`pipeline.reset()`) is available for development.

---

## 6. Escalation Logic

Escalation is evaluated **before** the LLM is asked to generate a customer-facing response — if any trigger fires, the agent does not attempt to answer and instead returns a handoff.

**Triggers (configurable in `src/config.py`):**

| Trigger | Condition | Config value |
|---|---|---|
| Low retrieval confidence | Best chunk similarity score `< 0.45` | `RETRIEVAL_CONFIDENCE_THRESHOLD` |
| Sensitive topic | Message contains billing/refund/legal/account-deletion keywords | `SENSITIVE_KEYWORDS` |
| Repeated frustration | 3+ consecutive turns classified as Frustrated User | `MAX_CONSECUTIVE_FRUSTRATION_TURNS` |

**Handoff summary** (`src/escalator.py::generate_handoff_summary`) is a structured JSON object containing: timestamp, detected persona, issue summary, escalation reason(s), retrieved source documents, retrieval confidence, conversation turn count, attempted steps so far, and a rule-based recommended next action for the human agent.

---

## 7. Setup Instructions

### Prerequisites
- Python 3.11+
- A free Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/persona-support-agent.git
cd persona-support-agent

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# then edit .env and paste your real GEMINI_API_KEY

# 5. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`. On first launch it automatically ingests every document in `/data` into a local ChromaDB store (`./chroma_db`) — this takes about 20-30 seconds and only happens once.

---

## 8. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key. Get one free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Never commit this — it belongs in `.env` (gitignored) locally, or in Streamlit Cloud's **Secrets** when deployed. |

---

## 9. Example Queries

| # | Query | Expected Persona | Expected Behavior |
|---|---|---|---|
| 1 | "Where is the guide to clear cookies? It's been an hour and nothing is loading on your interface!" | Frustrated User | Empathetic opener, simple numbered steps |
| 2 | "What are the header parameter requirements for your bearer token auth implementation?" | Technical Expert | Precise headers, error codes, code-level detail |
| 3 | "Our operational uptime is decreasing. We need a timeline of when billing disputes are resolved." | Business Executive | Brief, impact/timeline-focused — likely escalates (billing) |
| 4 | "I'm experiencing an issue with your database integration that's causing internal errors." | Technical Expert | Step-by-step resolution pathway from integrations doc |
| 5 | "My billing statement has unexpected duplicate charges. I demand an immediate refund!" | Frustrated User | **Escalates** — sensitive billing keyword triggers human handoff JSON |

---

## 10. Known Limitations & Future Improvements

**Current limitations:**
- Persona classification is single-turn — it doesn't yet use prior conversation context to refine its guess (e.g., a Technical Expert who later becomes frustrated is reclassified per-message, not tracked as a blended persona)
- Retrieval confidence score is derived from Chroma's distance metric, which is a reasonable proxy for cosine similarity but not a calibrated probability — thresholds were tuned empirically on this knowledge base and may need adjustment for a larger/different KB
- No persistent conversation storage across browser sessions (state lives in Streamlit's session state only)
- Sensitive-topic detection uses keyword matching, which is fast and transparent but can miss paraphrased billing/legal concerns that don't use the listed keywords

**Future improvements:**
- Add sentiment scoring as a secondary signal alongside persona classification
- Multi-turn memory that lets the agent reference earlier resolved/unresolved steps explicitly in the prompt
- Replace keyword-based sensitive-topic detection with a small classifier
- Add a feedback button (👍/👎) per response to collect labeled data for prompt refinement
- Swap the rule-based `_recommend_action` in `escalator.py` for an LLM-generated, context-aware recommendation

---

## 11. Project Structure

```
persona-support-agent/
├── data/                              # Knowledge base (9 docs: 7 text/markdown + 1 PDF)
├── src/
│   ├── config.py                      # Thresholds & model config
│   ├── classifier.py                  # Persona detection
│   ├── rag_pipeline.py                # Chunking, embedding, retrieval
│   ├── generator.py                   # Persona-adaptive response generation
│   └── escalator.py                   # Escalation rules & handoff JSON
├── app.py                             # Streamlit UI
├── generate_pdf.py                    # One-off script that generated the sample PDF doc
├── requirements.txt
├── .env.example
└── README.md
```
