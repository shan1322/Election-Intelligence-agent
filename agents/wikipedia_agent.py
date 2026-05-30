import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "ElectionIntelligenceBot/1.0 (https://github.com/shan1322)"}

def search_wikipedia(query: str) -> list:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 3,
        "format": "json",
        "utf8": 1
    }
    r = requests.get(WIKI_SEARCH, params=params, timeout=10, headers=HEADERS)
    r.raise_for_status()
    results = r.json().get("query", {}).get("search", [])
    return [r["title"] for r in results]

def get_full_page(title: str) -> str:
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": True,
        "titles": title,
        "format": "json",
        "utf8": 1
    }
    r = requests.get(WIKI_SEARCH, params=params, timeout=15, headers=HEADERS)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    page = list(pages.values())[0]
    return page.get("extract", "")

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def get_relevant_chunks(query: str, chunks: list, top_k: int = 3) -> list:
    if not chunks:
        return []
    docs = [query] + chunks
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(docs)
    scores = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [chunks[i] for i in top_indices]

def ask_wikipedia(query: str) -> dict:
    print(f"\n[Wikipedia] Query: {query}")

    # Step 1: Search
    titles = search_wikipedia(query)
    print(f"[Wikipedia] Found pages: {titles}")
    if not titles:
        return {"error": "No Wikipedia results found", "query": query}

    # Step 2: Fetch full page
    full_text = get_full_page(titles[0])
    if not full_text:
        return {"error": "Could not fetch page content", "query": query}
    print(f"[Wikipedia] Page length: {len(full_text.split())} words")

    # Step 3: Chunk
    chunks = chunk_text(full_text)
    print(f"[Wikipedia] Total chunks: {len(chunks)}")

    # Step 4: TF-IDF relevant chunks
    relevant = get_relevant_chunks(query, chunks, top_k=3)
    context = "\n\n".join(relevant)
    print(f"[Wikipedia] Relevant context preview: {context[:300]}...")

    return {
        "title": titles[0],
        "context": context,
        "full_length": len(full_text.split()),
        "chunks_used": len(relevant)
    }

if __name__ == "__main__":
    queries = [
        "Varanasi constituency election history",
        "Narendra Modi political career",
        "Bharatiya Janata Party history founding",
        "Amethi constituency Rahul Gandhi"
    ]
    for q in queries:
        result = ask_wikipedia(q)
        print(f"Title: {result.get('title')}")
        print(f"Context:\n{result.get('context', '')[:5000]}")
        print("-" * 50)
