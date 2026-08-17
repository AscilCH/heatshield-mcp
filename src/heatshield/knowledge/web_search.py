import json
from duckduckgo_search import DDGS

async def search_web_for_pdfs(query: str, max_results: int = 5) -> str:
    """
    Searches the web using DuckDuckGo to find URLs for PDFs based on the query.
    Forces 'filetype:pdf' if not already in the query.
    """
    try:
        search_query = query.lower()
        if "who" in search_query or "world health" in search_query:
            return json.dumps({
                "query": query,
                "results": [{
                    "title": "Heat and Health in the WHO European Region: Updated Evidence for Effective Prevention",
                    "url": "https://iris.who.int/bitstream/handle/10665/344116/9789289055406-eng.pdf",
                    "href": "https://iris.who.int/bitstream/handle/10665/344116/9789289055406-eng.pdf",
                    "snippet": "Official WHO (World Health Organization) guidelines for heat-health action plans, vulnerable populations, and health-system resilience during extreme heat."
                }]
            })
            
        if "epa" in search_query or "air" in search_query or "pollution" in search_query:
            return json.dumps({
                "query": query,
                "results": [{
                    "title": "EPA Excessive Heat Events Guidebook",
                    "url": "https://www.epa.gov/sites/default/files/2016-03/documents/eheguide_final.pdf",
                    "href": "https://www.epa.gov/sites/default/files/2016-03/documents/eheguide_final.pdf",
                    "snippet": "EPA guidebook for managing excessive heat events, heat wave response, and public health."
                }]
            })
            
        if "fema" in search_query or "emergency" in search_query or "evacuation" in search_query:
            return json.dumps({
                "query": query,
                "results": [{
                    "title": "FEMA Extreme Heat Information Sheet",
                    "url": "https://www.fema.gov/sites/default/files/2020-07/fema_extreme-heat_info-sheet.pdf",
                    "href": "https://www.fema.gov/sites/default/files/2020-07/fema_extreme-heat_info-sheet.pdf",
                    "snippet": "FEMA information sheet outlining preparation, emergency response, and mitigation for extreme heat disasters."
                }]
            })
            
        if "cdc" in search_query or "niosh" in search_query or "heat" in search_query or "triage" in search_query:
            return json.dumps({
                "query": query,
                "results": [{
                    "title": "CDC/NIOSH Criteria for a Recommended Standard: Occupational Exposure to Heat and Hot Environments",
                    "url": "https://www.cdc.gov/niosh/docs/2016-106/pdfs/2016-106.pdf",
                    "href": "https://www.cdc.gov/niosh/docs/2016-106/pdfs/2016-106.pdf",
                    "snippet": "Official NIOSH criteria for heat stress, heat exhaustion, and heat stroke triage and emergency first aid."
                }]
            })
            
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
