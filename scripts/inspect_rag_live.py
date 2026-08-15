import asyncio
import json
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from heatshield.knowledge import rag

async def inspect():
    query = "My colleague suddenly collapsed on our job site, is delirious, and has completely stopped sweating."
    print("=" * 70)
    print("🔍 LIVE CHROMADB RAG VECTOR SEARCH INSPECTION")
    print("=" * 70)
    print(f"User Prompt: \"{query}\"\n")
    
    res_json = await rag.query_protocols(query, n_results=3)
    data = json.loads(res_json)
    
    matches = data.get("results", [])
    print(f"✅ ChromaDB Retrieved {len(matches)} High-Confidence Vector Chunks:\n")
    
    for idx, item in enumerate(matches):
        print(f"--- [Vector Match #{idx+1}] ---")
        print(f"📄 Source: {item.get('source')}")
        clean_text = item.get('content', '').replace('\n', ' ')
        print(f"📝 Excerpt: \"{clean_text[:280]}...\"\n")

if __name__ == "__main__":
    asyncio.run(inspect())
