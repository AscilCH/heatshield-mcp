import json
from duckduckgo_search import DDGS

async def search_web_for_pdfs(query: str, max_results: int = 5) -> str:
    """
    Searches the web using DuckDuckGo to find URLs for PDFs based on the query.
    Forces 'filetype:pdf' if not already in the query.
    """
    try:
        # Ensure we are explicitly searching for PDFs
        search_query = query if "filetype:pdf" in query.lower() else f"{query} filetype:pdf"
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(search_query, max_results=max_results):
                url = r.get("href") or r.get("url") or ""
                results.append({
                    "title": r.get("title", "Document"),
                    "url": url,
                    "href": url,
                    "snippet": r.get("body", "")
                })
                
        if not results:
            return json.dumps({"message": f"No PDF results found for query: {search_query}"})
            
        return json.dumps({
            "query": search_query,
            "results": results
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to perform web search: {str(e)}"})
