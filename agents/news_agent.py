import requests
from ddgs import DDGS
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

HEADERS = {"User-Agent": "ElectionIntelligenceBot/1.0 (https://github.com/shan1322)"}

def fetch_article(url: str) -> str:
    """Fetch and extract clean text from article URL."""
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        # Get main text
        text = soup.get_text(separator=" ", strip=True)
        # Clean extra whitespace
        text = " ".join(text.split())
        return text
    except Exception as e:
        print(f"[News] Could not fetch {url}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> list:
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

def ask_news(query: str, max_results: int = 5, timelimit: str = "m") -> dict:
    """
    Fetch news, get full article content, extract relevant chunks.
    Returns context + sources for LLM.
    """
    print(f"\n[News] Query: {query}")

    # Step 1: Search news
    results = DDGS().news(
        query,
        max_results=max_results,
        timelimit=timelimit,
        region="in-en"
    )
    print(f"[News] Found {len(results)} articles")

    if not results:
        return {"error": "No news found", "query": query, "sources": []}

    # Step 2: Fetch full content from each article
    articles = []
    sources = []

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        date = r.get("date", "")
        snippet = r.get("body", "")

        print(f"[News] Fetching: {title[:60]}...")
        full_text = fetch_article(url)

        # Use snippet as fallback if fetch fails
        text = full_text if len(full_text) > 200 else snippet

        if text:
            articles.append(text)
            sources.append({
                "title": title,
                "url": url,
                "date": date,
                "snippet": snippet
            })

    if not articles:
        return {"error": "Could not fetch article content", "sources": []}

    # Step 3: Combine all article text and chunk
    combined = " ".join(articles)
    chunks = chunk_text(combined)
    print(f"[News] Total chunks from all articles: {len(chunks)}")

    # Step 4: TF-IDF relevant chunks
    relevant = get_relevant_chunks(query, chunks, top_k=4)
    context = "\n\n".join(relevant)

    print(f"[News] Relevant context preview: {context[:300]}...")

    return {
        "context": context,
        "sources": sources,
        "total_articles": len(articles)
    }

if __name__ == "__main__":
    queries = [
        "Narendra Modi latest political news",
        "BJP election results 2025",
        "Rahul Gandhi Congress party"
    ]
    for q in queries:
        result = ask_news(q)
        print(f"\nContext preview:\n{result.get('context', '')[:400]}")
        print(f"\nSources:")
        for s in result.get("sources", []):
            print(f"  - {s['title']} | {s['date']} | {s['url']}")
        print("=" * 60)
