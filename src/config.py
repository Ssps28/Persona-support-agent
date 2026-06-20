"""
config.py
Central configuration for the persona-adaptive support agent.
Keeping thresholds and model names here makes them easy to tune without
hunting through business logic.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# --- Models ---
GENERATION_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONALITY = 768

# --- Paths ---
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
COLLECTION_NAME = "support_kb"

# --- Chunking ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# --- Retrieval ---
TOP_K = 3

# --- Escalation thresholds ---
# Below this cosine-similarity score, retrieval is considered too weak to trust.
RETRIEVAL_CONFIDENCE_THRESHOLD = 0.45

# Topics that are always escalated regardless of retrieval quality, because they
# involve account-sensitive or irreversible actions a bot should not resolve alone.
SENSITIVE_KEYWORDS = [
    "refund", "duplicate charge", "duplicate charges", "chargeback",
    "cancel my account", "delete my account", "legal", "lawsuit",
    "gdpr", "unauthorized charge", "fraud", "dispute",
]

# Number of consecutive frustrated-persona turns (within one session) before
# we escalate even if individual retrieval looks fine.
MAX_CONSECUTIVE_FRUSTRATION_TURNS = 3

# --- Personas ---
PERSONAS = ["Technical Expert", "Frustrated User", "Business Executive"]
