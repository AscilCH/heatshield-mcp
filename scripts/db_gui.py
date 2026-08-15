import os
import json
import duckdb
import chromadb
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import webbrowser

app = FastAPI(title="HeatShield Database & Vector Studio")

DUCKDB_PATH = os.path.join("src", "heatshield", "spatial", ".spatial_cache.duckdb")
CHROMA_DIR = os.path.join("src", "heatshield", "knowledge", ".chroma_db")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    # 1. Fetch DuckDB Data
    duck_rows = []
    if os.path.exists(DUCKDB_PATH):
        try:
            con = duckdb.connect(DUCKDB_PATH, read_only=True)
            res = con.execute("SELECT location_key, cached_at, geojson_data FROM uhi_heatmap_cache").fetchall()
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

    # 2. Fetch ChromaDB Data
    chroma_docs = []
    if os.path.exists(CHROMA_DIR):
        try:
            client = chromadb.PersistentClient(path=CHROMA_DIR)
            col = client.get_collection("emergency_protocols")
            data = col.get(include=["documents", "metadatas", "embeddings"])
            for i in range(len(data.get("ids", []))):
                chroma_docs.append({
                    "id": data["ids"][i],
                    "source": data["metadatas"][i].get("source", "Unknown") if data.get("metadatas") else "Unknown",
                    "content": data["documents"][i] if data.get("documents") else "",
                    "dim": len(data["embeddings"][i]) if data.get("embeddings") is not None and len(data["embeddings"]) > i else 384
                })
        except Exception as e:
            chroma_docs = [{"error": str(e)}]

    # Render Modern Dark GUI HTML
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
            <h4 class="font-semibold text-slate-200 text-sm mb-2 flex items-center gap-2">
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
        <!-- Top Navbar -->
        <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-8 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-amber-500 flex items-center justify-center text-xl shadow-lg shadow-rose-500/20">🛡️</div>
                <div>
                    <h1 class="text-lg font-bold text-slate-100 flex items-center gap-2">
                        HeatShield <span class="text-xs px-2 py-0.5 bg-rose-500/10 text-rose-400 rounded-md font-mono border border-rose-500/20">Studio GUI</span>
                    </h1>
                    <p class="text-xs text-slate-400">Live Visual Inspector for DuckDB Spatial Cache & ChromaDB Vector Store</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <button onclick="location.reload()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition border border-slate-700 flex items-center gap-2">
                    🔄 Refresh Data
                </button>
            </div>
        </header>

        <main class="max-w-7xl mx-auto px-8 py-8 space-y-10">
            <!-- Section 1: DuckDB -->
            <section class="space-y-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">🦆</div>
                        <div>
                            <h2 class="text-lg font-bold text-slate-100">DuckDB Spatial Cache (<span class="font-mono text-emerald-400">.spatial_cache.duckdb</span>)</h2>
                            <p class="text-xs text-slate-400">Fast persistent column-store for Overpass Urban Heat Island GeoJSON polygons</p>
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

            <!-- Section 2: ChromaDB -->
            <section class="space-y-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold">🧠</div>
                        <div>
                            <h2 class="text-lg font-bold text-slate-100">ChromaDB Vector Store (<span class="font-mono text-rose-400">emergency_protocols</span>)</h2>
                            <p class="text-xs text-slate-400">High-dimensional vector embeddings for CDC/NIOSH Clinical Heat Triage (RAG)</p>
                        </div>
                    </div>
                    <span class="px-3 py-1 bg-rose-500/10 text-rose-400 rounded-full text-xs font-bold font-mono">
                        {len([d for d in chroma_docs if 'error' not in d])} Vectors Embedded
                    </span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {chroma_cards_html}
                </div>
            </section>
        </main>
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
