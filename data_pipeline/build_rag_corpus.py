"""
RAG Corpus Builder — Steps 1 to 3 only
========================================

STEP 1 - TEXT EXTRACTION
    Reads every PDF from budget_speeches/ and president_speeches/
    Uses pdfplumber to extract raw text
    Skips PDFs that fail or have less than 100 words

STEP 2 - CHUNKING
    Splits each document into paragraphs
    Each paragraph = one chunk = one retrieval unit
    Filters chunks shorter than 30 words (noise/headers)
    Adds metadata: source, year, filename, chunk_id

STEP 3 - SAVE TO JSON
    Saves ALL chunks from ALL documents into one single JSON file
    This is the master corpus
    BM25 will load this JSON at query time and index all chunks
    Qdrant will also use this same JSON in the next step
"""

import os
import json
import re
from pathlib import Path
from tqdm import tqdm
import pdfplumber

# ─── CONFIG ───────────────────────────────────────────────────────────────────

RAG_DATA_DIR = "/workspaces/codespaces-blank/election-intelligence/raw_data/rag_data"
CORPUS_PATH  = "/workspaces/codespaces-blank/election-intelligence/processed_data/rag_corpus.json"
MIN_CHUNK_WORDS = 30

os.makedirs(os.path.dirname(CORPUS_PATH), exist_ok=True)

# ─── STEP 1: TEXT EXTRACTION ──────────────────────────────────────────────────

def extract_text(pdf_path: str) -> str:
    """
    Extracts all text from a PDF using pdfplumber.
    Works well for text-based PDFs like budget and president speeches.
    Returns empty string if extraction fails.
    """
    try:
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as e:
        print(f"  [ERROR] {pdf_path}: {e}")
        return ""

# ─── STEP 2: CHUNKING ─────────────────────────────────────────────────────────

def chunk_by_paragraph(text: str, source: str, year: str, filename: str, start_id: int) -> list:
    """
    Splits document text into paragraphs.
    Each paragraph becomes one chunk.

    Why paragraphs and not fixed word count?
    Because budget speeches and president addresses are structured into
    paragraphs — each one is a complete policy point or announcement.
    Splitting by fixed word count would break ideas in the middle.

    Each chunk gets:
    - chunk_id  : unique integer ID across all documents
    - source    : "budget_speech" or "president_speech"
    - year      : "2019-20" or "2020" etc
    - filename  : original PDF name for reference
    - text      : the actual paragraph text
    """
    raw_paragraphs = re.split(r'\n{2,}', text)
    chunks = []
    chunk_id = start_id

    for para in raw_paragraphs:
        clean = " ".join(para.split())
        if len(clean.split()) < MIN_CHUNK_WORDS:
            continue
        chunks.append({
            "chunk_id": chunk_id,
            "source": source,
            "year": year,
            "filename": filename,
            "text": clean
        })
        chunk_id += 1

    return chunks

def parse_year(filename: str, source: str) -> str:
    """
    Extracts year label from filename.
    budget_speech_2019-20.pdf  →  2019-20
    president_speech_2020.pdf  →  2020
    """
    stem = Path(filename).stem
    if source == "budget_speech":
        return stem.replace("budget_speech_", "")
    return stem.replace("president_speech_", "")

# ─── STEP 3: BUILD + SAVE CORPUS ──────────────────────────────────────────────

def build_and_save():
    all_chunks = []
    chunk_id_counter = 0
    failed = []

    sources = [
        ("budget_speech",    os.path.join(RAG_DATA_DIR, "budget_speeches")),
        ("president_speech", os.path.join(RAG_DATA_DIR, "president_speeches")),
    ]

    for source, folder in sources:
        if not os.path.exists(folder):
            print(f"[SKIP] Not found: {folder}")
            continue

        pdfs = sorted([f for f in os.listdir(folder) if f.endswith(".pdf")])
        print(f"\n[{source}] {len(pdfs)} PDFs found")

        for filename in tqdm(pdfs, desc=source):
            pdf_path = os.path.join(folder, filename)
            year = parse_year(filename, source)

            # Step 1: extract text
            text = extract_text(pdf_path)
            if len(text.split()) < 100:
                failed.append(filename)
                continue

            # Step 2: chunk
            chunks = chunk_by_paragraph(text, source, year, filename, chunk_id_counter)
            if not chunks:
                failed.append(filename)
                continue

            all_chunks.extend(chunks)
            chunk_id_counter += len(chunks)

    # Step 3: save
    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"Total documents processed: {chunk_id_counter}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Failed PDFs: {len(failed)}")
    if failed:
        print(f"Failed: {failed}")
    print(f"Corpus saved to: {CORPUS_PATH}")

    # Print sample chunk
    if all_chunks:
        print(f"\nSample chunk:")
        print(json.dumps(all_chunks[0], indent=2))

if __name__ == "__main__":
    build_and_save()
