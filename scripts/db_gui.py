import os
import json
import duckdb
import chromadb
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import webbrowser

app = FastAPI(title="HeatShield Database & Vector Studio")

DUCKDB_PATH = os.path.join("src", "heatshield", "spatial", ".spatial_cache.duckdb")
CHROMA_DIR = os.path.join("src", "heatshield", "knowledge", ".chroma_db")

@app.get("/api/search-vectors")
async def search_vectors(q: str = Query(..., description="Semantic search query")):
    if not os.path.exists(CHROMA_DIR):
        return {"results": []}
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        col = client.get_collection("emergency_protocols")
        results = col.query(query_texts=[q], n_results=6)
        
        matches = []
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            ids = results["ids"][0]
            dists = results.get("distances", [[]])[0] if results.get("distances") else []
            
            for i in range(len(docs)):
                score = round(1.0 - dists[i], 3) if i < len(dists) else 0.95
                matches.append({
                    "id": ids[i],
                    "source": metas[i].get("source", "Document"),
                    "score": score,
                    "content": docs[i]
                })
        return {"query": q, "results": matches}
    except Exception as e:
        return {"error": str(e), "results": []}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    # 1. Fetch DuckDB Data
    duck_rows = []
    if os.path.exists(DUCKDB_PATH):
        try:
            con = duckdb.connect(DUCKDB_PATH, read_only=True)
            res = con.execute("SELECT location_key, cached_at, geojson_data FROM uhi_heatmap_cache ORDER BY cached_at DESC").fetchall()
            for r in res:
                geo = json.loads(r[2]) if r[2] else {}
                feature_count = len(geo.get("features", []))
                duck_rows.append({
                    "key": r[0],
                    "cached_at": str(r[1]),
                    "feature_count": feature_count,
                    "geojson_sample": json.dumps(geo, indent=2)[:300] + "..."
                })
            con.close()
        except Exception as e:
            duck_rows = [{"error": str(e)}]

    # 2. Fetch ChromaDB Collection Stats & Initial 12 Vectors
    chroma_docs = []
    total_vectors = 0
    if os.path.exists(CHROMA_DIR):
        try:
            client = chromadb.PersistentClient(path=CHROMA_DIR)
            col = client.get_collection("emergency_protocols")
            total_vectors = col.count()
            data = col.get(limit=12, include=["documents", "metadatas", "embeddings"])
            for i in range(len(data.get("ids", []))):
                chroma_docs.append({
                    "id": data["ids"][i],
                    "source": data["metadatas"][i].get("source", "Unknown") if data.get("metadatas") else "Unknown",
                    "content": data["documents"][i] if data.get("documents") else "",
                    "dim": len(data["embeddings"][i]) if data.get("embeddings") is not None and len(data["embeddings"]) > i else 384
                })
        except Exception as e:
            chroma_docs = [{"error": str(e)}]

    duck_rows_html = "".join([
        f"""
        <tr class="hover:bg-slate-800/50 border-b border-slate-800 transition-colors">
            <td class="p-4 font-mono text-emerald-400 font-semibold">{r.get('key')}</td>
            <td class="p-4 text-slate-300">{r.get('cached_at')}</td>
            <td class="p-4"><span class="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs font-semibold">{r.get('feature_count')} Polygons</span></td>
            <td class="p-4 text-xs font-mono text-slate-400 max-w-md truncate">{r.get('geojson_sample')}</td>
        </tr>
        """ for r in duck_rows if "error" not in r
    ]) or "<tr><td colspan='4' class='p-8 text-center text-slate-500'>No cached spatial records yet.</td></tr>"

    chroma_cards_html = "".join([
        f"""
        <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 hover:border-rose-500/40 transition-all shadow-lg">
            <div class="flex items-center justify-between mb-3">
                <span class="px-3 py-1 bg-rose-500/10 text-rose-400 rounded-full text-xs font-bold font-mono">{doc.get('id')}</span>
                <span class="text-xs text-slate-400 bg-slate-800/80 px-2.5 py-0.5 rounded-md font-mono">{doc.get('dim')}-dim vector</span>
            </div>
            <h4 class="font-semibold text-slate-200 text-sm mb-2 flex items-center gap-2 truncate">
                <span class="text-rose-400">📄</span> {doc.get('source')}
            </h4>
            <div class="p-3 bg-slate-950/60 rounded-xl text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto border border-slate-800/40">
{doc.get('content')}
            </div>
        </div>
        """ for doc in chroma_docs if "error" not in doc
    ]) or "<div class='p-8 text-center text-slate-500'>No embedded documents found.</div>"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HeatShield Database & Vector Studio</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
            pre, code, .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
        </style>
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen">
        <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-8 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-amber-500 flex items-center justify-center text-xl shadow-lg shadow-rose-500/20">🛡️</div>
                <div>
                    <h1 class="text-lg font-bold text-slate-100 flex items-center gap-2">
                        HeatShield <span class="text-xs px-2 py-0.5 bg-rose-500/10 text-rose-400 rounded-md font-mono border border-rose-500/20">Vector Studio</span>
                    </h1>
                    <p class="text-xs text-slate-400">Live Visual Explorer for ChromaDB ({total_vectors} vectors) & DuckDB ({len(duck_rows)} records)</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <button onclick="location.reload()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition border border-slate-700 flex items-center gap-2">
                    🔄 Refresh Studio
                </button>
            </div>
        </header>

        <main class="max-w-7xl mx-auto px-8 py-8 space-y-10">
            <!-- ChromaDB Interactive Vector Search Section -->
            <section class="space-y-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold">🧠</div>
                        <div>
                            <h2 class="text-lg font-bold text-slate-100">ChromaDB Vector Store (<span class="font-mono text-rose-400">emergency_protocols</span>)</h2>
                            <p class="text-xs text-slate-400">High-dimensional 384-dim semantic embeddings for CDC/NIOSH & OSHA guidelines</p>
                        </div>
                    </div>
                    <span class="px-3.5 py-1.5 bg-rose-500/10 text-rose-400 rounded-full text-xs font-bold font-mono border border-rose-500/20">
                        {total_vectors} Vectors Indexed
                    </span>
                </div>

                <!-- Live Vector Search Bar -->
                <div class="p-4 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl flex gap-3">
                    <input id="searchQuery" type="text" placeholder="Type a symptom or question (e.g. 'collapsed stopped sweating', 'hydration rate at 40C')..." 
                           class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-rose-500 text-slate-100 font-mono"
                           onkeydown="if(event.key === 'Enter') runSearch()" />
                    <button onclick="runSearch()" class="px-6 py-3 bg-gradient-to-r from-rose-500 to-amber-500 hover:from-rose-600 hover:to-amber-600 text-white font-semibold text-sm rounded-xl transition shadow-lg shadow-rose-500/20">
                        ⚡ Search Vectors
                    </button>
                </div>

                <div id="searchResults" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {chroma_cards_html}
                </div>
            </section>

            <!-- DuckDB Section -->
            <section class="space-y-4 pt-6 border-t border-slate-800/80">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">🦆</div>
                        <div>
                            <h2 class="text-lg font-bold text-slate-100">DuckDB Spatial Cache (<span class="font-mono text-emerald-400">.spatial_cache.duckdb</span>)</h2>
                            <p class="text-xs text-slate-400">Persistent spatial grid table for Overpass Urban Heat Island GeoJSON polygons</p>
                        </div>
                    </div>
                    <span class="px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs font-bold font-mono">
                        {len([r for r in duck_rows if 'error' not in r])} Records Cached
                    </span>
                </div>

                <div class="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
                    <table class="w-full text-left border-collapse text-sm">
                        <thead class="bg-slate-900 border-b border-slate-800 text-slate-400 text-xs font-mono uppercase tracking-wider">
                            <tr>
                                <th class="p-4">Spatial Grid Key</th>
                                <th class="p-4">Cached Timestamp</th>
                                <th class="p-4">Payload Size</th>
                                <th class="p-4">GeoJSON Preview</th>
                            </tr>
                        </thead>
                        <tbody>
                            {duck_rows_html}
                        </tbody>
                    </table>
                </div>
            </section>
        </main>

        <script>
            async function runSearch() {{
                const q = document.getElementById('searchQuery').value.trim();
                if (!q) return;
                const container = document.getElementById('searchResults');
                container.innerHTML = '<div class="p-8 text-center text-slate-400 col-span-2">🔍 Executing 384-dimensional cosine similarity search across {total_vectors} vectors...</div>';
                
                try {{
                    const res = await fetch(`/api/search-vectors?q=${{encodeURIComponent(q)}}`);
                    const data = await res.json();
                    
                    if (!data.results || data.results.length === 0) {{
                        container.innerHTML = '<div class="p-8 text-center text-slate-500 col-span-2">No matching vector chunks found.</div>';
                        return;
                    }}
                    
                    container.innerHTML = data.results.map((r, i) => `
                        <div class="p-5 rounded-2xl bg-slate-900/90 border border-rose-500/40 shadow-xl animate-fadeIn">
                            <div class="flex items-center justify-between mb-3">
                                <span class="px-3 py-1 bg-rose-500/20 text-rose-300 rounded-full text-xs font-bold font-mono">${{r.id}}</span>
                                <span class="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-md font-mono font-bold">Similarity: ${{Math.round(r.score * 100)}}%</span>
                            </div>
                            <h4 class="font-semibold text-slate-200 text-sm mb-2 flex items-center gap-2 truncate">
                                <span class="text-rose-400">📄</span> ${{r.source}}
                            </h4>
                            <div class="p-3 bg-slate-950/70 rounded-xl text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto border border-slate-800/60">
${{r.content}}
                            </div>
                        </div>
                    `).join('');
                }} catch (e) {{
                    container.innerHTML = `<div class="p-8 text-center text-rose-400 col-span-2">Search error: ${{e.message}}</div>`;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Launching HeatShield Database & Vector Studio GUI...")
    print("👉 Open your browser at: http://127.0.0.1:8080")
    print("=" * 60)
    webbrowser.open("http://127.0.0.1:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080)
