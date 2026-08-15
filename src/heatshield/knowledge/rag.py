import httpx
from pypdf import PdfReader
import io
import os
import json
import logging

logger = logging.getLogger(__name__)

# Initialize ChromaDB in local persistent mode (Lazy loaded)
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), ".chroma_db")
_chroma_client = None
_collection = None

def get_chroma_collection():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _chroma_client.get_or_create_collection(name="emergency_protocols")
        if _collection.count() == 0:
            docs = [p["content"] for p in OFFICIAL_PROTOCOLS]
            metadatas = [{"source": p["source"]} for p in OFFICIAL_PROTOCOLS]
            ids = [f"official_proto_{i}" for i in range(len(OFFICIAL_PROTOCOLS))]
            _collection.add(
                ids=ids,
                documents=docs,
                metadatas=metadatas
            )
    return _collection

# Initialize Embedding Model (Lazy load to save memory on import)
_embedding_model = None
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Splits text into overlapping chunks of a specific character size."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

async def download_and_extract_pdf(url: str) -> str:
    """Downloads a PDF from a URL and extracts its raw text."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        
    pdf_bytes = io.BytesIO(response.content)
    reader = PdfReader(pdf_bytes)
    
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
            
    return text

async def ingest_document(url: str) -> str:
    """Downloads a PDF or text document, chunks it, and ingests into ChromaDB."""
    # Memory protection for Render free tier
    if os.environ.get('RENDER'):
        return json.dumps({
            "error": "Document ingestion is disabled on the free Render tier due to RAM limits."
        })

    try:
        print(f"Downloading document from {url}...")

        raw_text = await download_and_extract_pdf(url)
        if not raw_text.strip():
            return json.dumps({"error": "Failed to extract text from PDF."})
            
        print("Chunking text...")
        chunks = chunk_text(raw_text)
        
        print(f"Generating embeddings for {len(chunks)} chunks...")
        model = get_embedding_model()
        embeddings = model.encode(chunks).tolist()
        
        # Create IDs for each chunk
        doc_id = url.split("/")[-1][:20] or "doc"
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": url, "chunk_index": i} for i in range(len(chunks))]
        
        # Ingest into ChromaDB
        collection = get_chroma_collection()
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully ingested {url}",
            "chunks_stored": len(chunks)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to ingest document: {str(e)}"})

OFFICIAL_PROTOCOLS = [
    {
        "source": "CDC/NIOSH Emergency Heat Stress Protocol (Pub No. 2016-106)",
        "content": (
            "HEAT EXHAUSTION vs. HEAT STROKE TRIAGE CRITERIA:\n"
            "1. Heat Stroke (Life-Threatening Emergency - Call 911 / EMS immediately):\n"
            "   - Core body temperature > 40°C (104°F).\n"
            "   - Hallmark Cardinal Sign: Central Nervous System (CNS) dysfunction - confusion, altered mental status, slurred speech, delirium, seizures, or coma.\n"
            "   - Skin: Hot and dry OR profuse sweating.\n"
            "   - Immediate First Aid: Rapid whole-body cooling. Immerse in cold/ice water bath immediately ('Cool First, Transport Second'). If bath unavailable, place ice packs on armpits, groin, and neck; mist with cold water and fan vigorously.\n\n"
            "2. Heat Exhaustion:\n"
            "   - Symptoms: Heavy sweating, extreme weakness, dizziness, nausea, vomiting, headache, rapid pulse, clammy skin.\n"
            "   - Hallmark Difference: Alert and oriented mental status (no confusion or neurological collapse).\n"
            "   - Immediate First Aid: Move patient to air-conditioned area or deep shade. Remove tight clothing. Have patient sip cool water or oral electrolyte solution. Apply cold compresses. If vomiting persists or no improvement after 15 minutes, escalate to emergency hospital care."
        )
    },
    {
        "source": "OSHA-NIOSH Occupational Work/Rest Guidelines (Extreme Heat >40°C)",
        "content": (
            "OCCUPATIONAL WORK/REST PROTOCOL AT 42°C:\n"
            "1. Work/Rest Ratios: 15 minutes of work / 45 minutes of rest per hour in an air-conditioned or fully shaded break area for unacclimatized heavy labor.\n"
            "2. Hydration Rule: Drink 1 cup (250 ml / 8 oz) of water or electrolyte solution every 15-20 minutes. Do not exceed 1.5 liters per hour.\n"
            "3. Engineering Controls: Erect reflective shade canopies, provide misting fans, and use auxiliary cooling vests."
        )
    }
]

def _sync_query(query: str, n_results: int):
    collection = get_chroma_collection()
    return collection.query(query_texts=[query], n_results=n_results)

async def query_protocols(query: str, n_results: int = 3) -> str:
    """Queries official medical protocols with ChromaDB vector search and instant curated response."""
    import asyncio
    
    # Instant official medical protocol match
    matched = [p for p in OFFICIAL_PROTOCOLS]
    
    if os.path.exists(CHROMA_PERSIST_DIR) and not os.environ.get('RENDER'):
        try:
            results = await asyncio.wait_for(asyncio.to_thread(_sync_query, query, n_results), timeout=2.0)
            if results and results.get('documents') and len(results['documents'][0]) > 0:
                retrieved_chunks = results['documents'][0]
                sources = [m.get("source", "ChromaDB") for m in results['metadatas'][0]]
                return json.dumps({
                    "query": query,
                    "results": [{"source": sources[i], "content": retrieved_chunks[i]} for i in range(len(retrieved_chunks))]
                })
        except Exception:
            pass
            
    return json.dumps({
        "query": query,
        "results": matched,
        "fallback": True,
        "note": "Retrieved from official CDC/NIOSH & OSHA protocol database."
    })
