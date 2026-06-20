"""
rag_pipeline.py
Handles document ingestion (parsing, chunking, embedding) and retrieval
(query embedding + cosine similarity search) against a persistent ChromaDB
vector store.
"""

import os
import glob
import time
import chromadb
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
        self.chroma_client = chromadb.PersistentClient(path=db_dir or config.CHROMA_DB_DIR)
        self.collection = self.chroma_client.get_or_create_collection(name=config.COLLECTION_NAME)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )

    # ---------- Embedding ----------

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

    # ---------- Ingestion ----------

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
        """Split a document's text into chunks and add them to the vector DB."""
        chunks = self.splitter.split_text(content)
        for idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            embedding = self.get_embedding(chunk)
            chunk_id = f"{doc_name}_chunk_{idx}"
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[{"source": doc_name, "chunk_index": idx}],
                documents=[chunk],
            )

    def ingest_directory(self, data_dir: str = None, progress_callback=None):
        """
        Ingest every supported file in the data directory.
        progress_callback(current, total, filename) is called after each file,
        useful for showing progress in a Streamlit UI.
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

        return len(filepaths)

    def is_indexed(self) -> bool:
        """Check whether the collection already has documents indexed."""
        return self.collection.count() > 0

    def reset(self):
        """Wipe the collection — useful for re-ingestion during development."""
        self.chroma_client.delete_collection(name=config.COLLECTION_NAME)
        self.collection = self.chroma_client.get_or_create_collection(name=config.COLLECTION_NAME)

    # ---------- Retrieval ----------

    def retrieve_context(self, query: str, top_k: int = None) -> list:
        """
        Embed the query and perform a cosine-similarity search against the
        indexed chunks. Returns a list of {text, source, chunk_index, score}.
        """
        top_k = top_k or config.TOP_K
        query_vector = self.get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )

        retrieved_items = []
        if results and results.get("documents") and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i] if results.get("distances") else 1.0
                # Chroma's default space is L2 by default for embeddings added this way,
                # but since we control embedding generation and these are normalized
                # semantic vectors, we treat (1 - distance) as a similarity proxy.
                similarity = max(0.0, 1.0 - distance)
                retrieved_items.append({
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i]["source"],
                    "chunk_index": results["metadatas"][0][i]["chunk_index"],
                    "score": round(similarity, 4),
                })
        return retrieved_items


if __name__ == "__main__":
    pipeline = LocalRAGPipeline()
    if not pipeline.is_indexed():
        print("Indexing documents...")
        count = pipeline.ingest_directory()
        print(f"Ingested {count} documents.")
    else:
        print("Collection already indexed.")

    test_query = "How do I reset my password?"
    results = pipeline.retrieve_context(test_query)
    for r in results:
        print(f"\n[{r['source']} | score={r['score']}]\n{r['text'][:200]}...")