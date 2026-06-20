"""
rag_pipeline.py
Handles document ingestion (parsing, chunking, embedding) and retrieval
(query embedding + cosine similarity search) against a local FAISS vector
index, persisted to disk as a flat index + metadata sidecar file.
"""

import os
import glob
import json
import time
import pickle
import numpy as np
import faiss
from pypdf import PdfReader
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from google import genai
from google.genai import types

from src import config


class LocalRAGPipeline:
    def __init__(self, db_dir: str = None):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.db_dir = db_dir or config.CHROMA_DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)

        self.index_path = os.path.join(self.db_dir, "faiss_index.bin")
        self.meta_path = os.path.join(self.db_dir, "faiss_meta.pkl")

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )

        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatIP(config.EMBEDDING_DIMENSIONALITY)
            self.metadata = []

    def _save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def get_embedding(self, text: str, retries: int = 4) -> list:
        """Call Gemini's embedding model, with simple exponential backoff."""
        for attempt in range(retries):
            try:
                response = self.client.models.embed_content(
                    model=config.EMBEDDING_MODEL,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=config.EMBEDDING_DIMENSIONALITY
                    ),
                )
                return response.embeddings[0].values
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep((2 ** attempt) + 0.5)

    def _read_file(self, filepath: str) -> str:
        """Parse a single file (.txt, .md, .pdf) into raw text."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext in (".txt", ".md"):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".pdf":
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
            return text
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def ingest_document(self, doc_name: str, content: str):
        """Split a document's text into chunks, embed, and add to the FAISS index."""
        chunks = self.splitter.split_text(content)
        for idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            embedding = self.get_embedding(chunk)
            vec = np.array([embedding], dtype="float32")
            faiss.normalize_L2(vec)
            self.index.add(vec)
            self.metadata.append({
                "source": doc_name,
                "chunk_index": idx,
                "text": chunk,
            })

    def ingest_directory(self, data_dir: str = None, progress_callback=None):
        """
        Ingest every supported file in the data directory.
        progress_callback(current, total, filename) is called after each file.
        """
        data_dir = data_dir or config.DATA_DIR
        filepaths = sorted(
            glob.glob(os.path.join(data_dir, "*.txt"))
            + glob.glob(os.path.join(data_dir, "*.md"))
            + glob.glob(os.path.join(data_dir, "*.pdf"))
        )

        for i, filepath in enumerate(filepaths):
            doc_name = os.path.basename(filepath)
            content = self._read_file(filepath)
            self.ingest_document(doc_name, content)
            if progress_callback:
                progress_callback(i + 1, len(filepaths), doc_name)

        self._save_index()
        return len(filepaths)

    def is_indexed(self) -> bool:
        """Check whether the index already has vectors stored."""
        return self.index is not None and self.index.ntotal > 0

    def reset(self):
        """Wipe the index — useful for re-ingestion during development."""
        self.index = faiss.IndexFlatIP(config.EMBEDDING_DIMENSIONALITY)
        self.metadata = []
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.meta_path):
            os.remove(self.meta_path)

    def retrieve_context(self, query: str, top_k: int = None) -> list:
        """
        Embed the query and perform a cosine-similarity search against the
        indexed chunks. Returns a list of {text, source, chunk_index, score}.
        """
        top_k = top_k or config.TOP_K
        if not self.is_indexed():
            return []

        query_vector = self.get_embedding(query)
        vec = np.array([query_vector], dtype="float32")
        faiss.normalize_L2(vec)

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(vec, k)

        retrieved_items = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = self.metadata[idx]
            retrieved_items.append({
                "text": meta["text"],
                "source": meta["source"],
                "chunk_index": meta["chunk_index"],
                "score": round(float(score), 4),
            })
        return retrieved_items


if __name__ == "__main__":
    pipeline = LocalRAGPipeline()
    if not pipeline.is_indexed():
        print("Indexing documents...")
        count = pipeline.ingest_directory()
        print(f"Ingested {count} documents.")
    else:
        print("Index already built.")

    test_query = "How do I reset my password?"
    results = pipeline.retrieve_context(test_query)
    for r in results:
        print(f"\n[{r['source']} | score={r['score']}]\n{r['text'][:200]}...")
