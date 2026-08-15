import duckdb
import chromadb
import json
import os
import sys

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DUCKDB_PATH = os.path.join("src", "heatshield", "spatial", ".spatial_cache.duckdb")
CHROMA_DIR = os.path.join("src", "heatshield", "knowledge", ".chroma_db")

print("=" * 70)
print("🔍 HEATSHIELD DATABASE INSPECTOR (DUCKDB & CHROMADB)")
print("=" * 70)

# ==========================================
# 1. INSPECT DUCKDB SPATIAL CACHE
# ==========================================
print("\n[1] 🦆 DUCKDB SPATIAL CACHE INSPECTION:")
print(f"    File: {DUCKDB_PATH}")

if os.path.exists(DUCKDB_PATH):
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        tables = con.execute("SHOW TABLES").fetchall()
        print(f"    Tables found: {[t[0] for t in tables]}")
        
        row_count = con.execute("SELECT COUNT(*) FROM uhi_heatmap_cache").fetchone()[0]
        print(f"    Total Cached Spatial Heatmaps: {row_count}")
        
        if row_count > 0:
            print("\n    Stored Spatial Records in DuckDB:")
            rows = con.execute("SELECT location_key, cached_at, LENGTH(geojson_data) FROM uhi_heatmap_cache").fetchall()
            for key, timestamp, length in rows:
                print(f"    - Grid Key: {key:20} | Cached At: {str(timestamp):19} | Size: {length:6} bytes")
        con.close()
    except Exception as e:
        print(f"    Error reading DuckDB: {e}")
else:
    print("    DuckDB cache file not created yet (will initialize on first UHI query).")

# ==========================================
# 2. INSPECT CHROMADB VECTOR DATABASE (RAG)
# ==========================================
print("\n" + "-" * 70)
print("[2] 🧠 CHROMADB VECTOR DATABASE (RAG) INSPECTION:")
print(f"    Directory: {CHROMA_DIR}")

if os.path.exists(CHROMA_DIR):
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        collections = client.list_collections()
        print(f"    Collections found: {[c.name for c in collections]}")
        
        for col_info in collections:
            col = client.get_collection(col_info.name)
            count = col.count()
            print(f"\n    📦 Collection '{col.name}' (Total Vectors: {count}):")
            
            if count > 0:
                data = col.get(include=["documents", "metadatas", "embeddings"])
                for i in range(min(5, count)):
                    doc_id = data["ids"][i]
                    meta = data["metadatas"][i] if data.get("metadatas") else {}
                    doc_preview = data["documents"][i][:120].replace("\n", " ") if data.get("documents") else ""
                    has_emb = "Yes (384-dim)" if data.get("embeddings") is not None and len(data["embeddings"]) > i else "Stored"
                    
                    print(f"\n      [Vector #{i+1}] ID: {doc_id}")
                    print(f"      Source: {meta.get('source', 'Unknown')}")
                    print(f"      Vector Embedding: {has_emb}")
                    print(f"      Content Preview: \"{doc_preview}...\"")
    except Exception as e:
        print(f"    Error reading ChromaDB: {e}")
else:
    print("    ChromaDB directory not created yet.")

print("\n" + "=" * 70)
print("✅ INSPECTION COMPLETE")
print("=" * 70)
