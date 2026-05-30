"""
Embed and Upload to ChromaDB
=============================

STEP 1 - LOAD CORPUS
    Loads the rag_corpus.json we built earlier
    This has all 3229 chunks with metadata

STEP 2 - LOAD EMBEDDING MODEL
    Uses sentence-transformers all-MiniLM-L6-v2
    Free, runs locally, 256 token max per chunk
    Converts each chunk's text into a 384-dimensional vector

STEP 3 - SETUP CHROMADB
    Creates a persistent ChromaDB collection on disk
    Collection name: election_rag
    Stores: vectors + original text + metadata (source, year, filename)

STEP 4 - EMBED + UPLOAD IN BATCHES
    Embeds chunks in batches of 64 for memory efficiency
    Uploads to ChromaDB with chunk_id as the document ID
    Skips if collection already has data (resume friendly)
"""

import json
import os
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import chromadb

# ─── CONFIG ───────────────────────────────────────────────────────────────────

CORPUS_PATH  = "/workspaces/codespaces-blank/election-intelligence/processed_data/rag_corpus.json"
CHROMA_DIR   = "/workspaces/codespaces-blank/election-intelligence/processed_data/chromadb"
COLLECTION   = "election_rag"
EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE   = 64

# ─── STEP 1: LOAD CORPUS ──────────────────────────────────────────────────────

print("Step 1: Loading corpus...")
with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)
print(f"  Loaded {len(chunks)} chunks")

# ─── STEP 2: LOAD EMBEDDING MODEL ─────────────────────────────────────────────

print("\nStep 2: Loading embedding model...")
model = SentenceTransformer(EMBED_MODEL)
print(f"  Model loaded: {EMBED_MODEL}")

# ─── STEP 3: SETUP CHROMADB ───────────────────────────────────────────────────

print("\nStep 3: Setting up ChromaDB...")
os.makedirs(CHROMA_DIR, exist_ok=True)
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION,
    metadata={"hnsw:space": "cosine"}
)
print(f"  Collection: {COLLECTION}")
print(f"  Existing docs: {collection.count()}")

# Skip if already uploaded
if collection.count() >= len(chunks):
    print("  Already uploaded. Skipping.")
else:
    # ─── STEP 4: EMBED + UPLOAD IN BATCHES ────────────────────────────────────

    print(f"\nStep 4: Embedding and uploading {len(chunks)} chunks in batches of {BATCH_SIZE}...")

    for i in tqdm(range(0, len(chunks), BATCH_SIZE)):
        batch = chunks[i:i+BATCH_SIZE]

        ids       = [str(c["chunk_id"]) for c in batch]
        texts     = [c["text"] for c in batch]
        metadatas = [{"source": c["source"], "year": c["year"], "filename": c["filename"]} for c in batch]

        # Embed
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        # Upload
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

    print(f"\nDone. Total docs in ChromaDB: {collection.count()}")

# ─── VERIFY ───────────────────────────────────────────────────────────────────

print("\nVerification — test query: 'farmers agriculture subsidy'")
results = collection.query(
    query_embeddings=model.encode(["farmers agriculture subsidy"]).tolist(),
    n_results=3
)
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"\n  [{meta['source']} {meta['year']}]")
    print(f"  {doc[:200]}...")
