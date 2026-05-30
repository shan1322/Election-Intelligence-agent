import json
import os
import requests

HF_TOKEN   = os.getenv("HF_TOKEN", "")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL      = "meta-llama/Llama-3.1-8B-Instruct"

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_PATH = os.path.join(BASE, "processed_data", "rag_corpus.json")
CHROMA_DIR  = os.path.join(BASE, "processed_data", "chromadb")
COLLECTION  = "election_rag"

# Lazy loaded — only initialized when first RAG query comes in
_corpus = None
_bm25 = None
_embed = None
_chroma = None

def _init():
    global _corpus, _bm25, _embed, _chroma
    if _corpus is not None:
        return

    print("[RAG] Loading corpus and building BM25 index...")
    from rank_bm25 import BM25Okapi
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        _corpus = json.load(f)
    tokenized = [c["text"].lower().split() for c in _corpus]
    _bm25 = BM25Okapi(tokenized)
    print(f"[RAG] BM25 index built on {len(_corpus)} chunks")

    print("[RAG] Loading embedding model...")
    from sentence_transformers import SentenceTransformer
    _embed = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    print("[RAG] Connecting to ChromaDB...")
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    _chroma = client.get_collection(COLLECTION)
    print(f"[RAG] Ready. ChromaDB has {_chroma.count()} chunks")

def retrieve(query: str, top_k: int = 5) -> list:
    _init()
    bm25_scores = _bm25.get_scores(query.lower().split())
    bm25_top = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
    bm25_chunks = {_corpus[i]["chunk_id"]: _corpus[i] for i in bm25_top}

    query_vec = _embed.encode([query]).tolist()
    vec_results = _chroma.query(query_embeddings=query_vec, n_results=top_k)
    vec_chunks = {}
    for doc, meta, cid in zip(vec_results["documents"][0], vec_results["metadatas"][0], vec_results["ids"][0]):
        chunk_id = int(cid)
        vec_chunks[chunk_id] = {
            "chunk_id": chunk_id,
            "source": meta["source"],
            "year": meta["year"],
            "filename": meta["filename"],
            "text": doc
        }

    combined = {**bm25_chunks, **vec_chunks}
    return list(combined.values())[:top_k]

def ask_rag(query: str) -> dict:
    print(f"\n[RAG] Query: {query}")
    chunks = retrieve(query)
    print(f"[RAG] Retrieved {len(chunks)} chunks")

    context = ""
    for c in chunks:
        context += f"\n[{c['source'].upper()} {c['year']}]\n{c['text']}\n"

    system = """You are an expert on Indian political history, budgets and government policy.
Answer the user's question using ONLY the provided context.
Always cite your sources at the end like: Source: Budget Speech 2019, President Address 2020.
If the context does not contain the answer, say so honestly."""

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ],
        "max_tokens": 500,
        "temperature": 0.2
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    answer = response.json()["choices"][0]["message"]["content"].strip()
    sources = list(set(f"{c['source'].replace('_', ' ').title()} {c['year']}" for c in chunks))

    return {"answer": answer, "sources": sources, "chunks_used": len(chunks)}
