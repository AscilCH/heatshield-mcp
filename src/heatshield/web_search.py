import json
from duckduckgo_search import DDGS

async def search_web_for_pdfs(query: str, max_results: int = 5) -> str:
    """
    Uses DuckDuckGo to search the web for PDF documents.
    """
    try:
        results = []
        with DDGS() as ddgs:
            # We enforce that the query should include 'filetype:pdf'
            # But just in case the LLM forgets, we don't strictly append it to avoid doubling it up,
            # we just trust the LLM's prompt.
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
        
        if not results:
            return json.dumps({"status": "error", "message": "No documents found."})
            
        return json.dumps({
            "status": "success", 
            "message": f"Found {len(results)} potential documents.", 
            "results": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Search failed: {str(e)}"})
