"""
RAG Agent — Hybrid Retrieval
=============================

How it works:
1. User asks a question
2. BM25 searches all chunks by keyword matching — finds exact term matches
3. ChromaDB searches by vector similarity — finds semantically similar chunks
4. Results from both are combined and deduplicated by chunk_id
5. Top chunks are passed to LLM as context
6. LLM generates answer with source citations

Why hybrid?
- BM25 alone: misses semantic meaning ("farm support" won't match "agricultural subsidy")
- Vector alone: misses exact terms ("Budget 2019" won't reliably match year)
- Together: best of both worlds
"""

import json
import os
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import chromadb
import requests

# ─── CONFIG ───────────────────────────────────────────────────────────────────

CORPUS_PATH = "/workspaces/codespaces-blank/election-intelligence/processed_data/rag_corpus.json"
CHROMA_DIR  = "/workspaces/codespaces-blank/election-intelligence/processed_data/chromadb"
COLLECTION  = "election_rag"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_TOKEN    = os.getenv("HF_TOKEN", "")
HF_API_URL  = "https://router.huggingface.co/v1/chat/completions"
MODEL       = "meta-llama/Llama-3.1-8B-Instruct"
TOP_K       = 5  # number of chunks to retrieve

# ─── LOAD CORPUS + BUILD BM25 INDEX ───────────────────────────────────────────

print("[RAG] Loading corpus and building BM25 index...")
with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    CORPUS = json.load(f)

# BM25 needs tokenized text — just split by whitespace
tokenized = [c["text"].lower().split() for c in CORPUS]
BM25_INDEX = BM25Okapi(tokenized)
print(f"[RAG] BM25 index built on {len(CORPUS)} chunks")

# ─── LOAD EMBEDDING MODEL + CHROMADB ──────────────────────────────────────────

print("[RAG] Loading embedding model...")
EMBED = SentenceTransformer(EMBED_MODEL)

print("[RAG] Connecting to ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_DIR)
CHROMA = client.get_collection(COLLECTION)
print(f"[RAG] Ready. ChromaDB has {CHROMA.count()} chunks")

# ─── RETRIEVAL ────────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> list:
    """
    Hybrid retrieval: BM25 + ChromaDB vector search.
    Returns top_k most relevant chunks.
    """
    # BM25 retrieval — keyword matching
    bm25_scores = BM25_INDEX.get_scores(query.lower().split())
    bm25_top = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
    bm25_chunks = {CORPUS[i]["chunk_id"]: CORPUS[i] for i in bm25_top}

    # Vector retrieval — semantic matching
    query_vec = EMBED.encode([query]).tolist()
    vec_results = CHROMA.query(query_embeddings=query_vec, n_results=top_k)
    vec_chunks = {}
    for doc, meta, cid in zip(
        vec_results["documents"][0],
        vec_results["metadatas"][0],
        vec_results["ids"][0]
    ):
        chunk_id = int(cid)
        vec_chunks[chunk_id] = {
            "chunk_id": chunk_id,
            "source": meta["source"],
            "year": meta["year"],
            "filename": meta["filename"],
            "text": doc
        }

    # Combine — union of both, deduplicated by chunk_id
    combined = {**bm25_chunks, **vec_chunks}
    return list(combined.values())[:top_k]

# ─── LLM CALL ─────────────────────────────────────────────────────────────────

def call_llm(query: str, context_chunks: list) -> str:
    """Passes retrieved chunks to LLM and gets answer with citations."""
    context = ""
    for c in context_chunks:
        context += f"\n[{c['source'].upper()} {c['year']}]\n{c['text']}\n"

    system = """You are an expert on Indian political history, budgets and government policy.
Answer the user's question using ONLY the provided context.
Always cite your sources at the end like: Source: Budget Speech 2019, President Address 2020.
If the context does not contain the answer, say so honestly."""

    user = f"""Context:\n{context}\n\nQuestion: {query}"""

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "max_tokens": 500,
        "temperature": 0.2
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

# ─── MAIN FUNCTION ────────────────────────────────────────────────────────────

def ask_rag(query: str) -> dict:
    """Main entry point. Retrieve + generate answer."""
    print(f"\n[RAG] Query: {query}")

    chunks = retrieve(query)
    print(f"[RAG] Retrieved {len(chunks)} chunks")
    for c in chunks:
        print(f"  [{c['source']} {c['year']}] {c['text'][:80]}...")

    answer = call_llm(query, chunks)
    sources = list(set(f"{c['source'].replace('_', ' ').title()} {c['year']}" for c in chunks))

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks)
    }

if __name__ == "__main__":
    queries = [
        "How has defence spending changed over the years?",
    ]
    for q in queries:
        result = ask_rag(q)
        print(f"\nAnswer: {result['answer']}")
        print(f"Sources: {result['sources']}")
        print("=" * 60)
