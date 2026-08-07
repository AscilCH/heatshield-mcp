import chromadb
from sentence_transformers import SentenceTransformer
import httpx
from pypdf import PdfReader
import io
import os
import json

# Initialize ChromaDB in local persistent mode
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), ".chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
collection = chroma_client.get_or_create_collection(name="emergency_protocols")

# Initialize Embedding Model (Lazy load to save memory on import)
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
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
    """Orchestrates downloading, extracting, chunking, embedding, and storing a PDF."""
    try:
        print(f"Downloading PDF from {url}...")
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
        
        print("Saving to ChromaDB...")
        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully ingested {url}",
            "chunks_stored": len(chunks)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to ingest document: {str(e)}"})

async def query_protocols(query: str, n_results: int = 3) -> str:
    """Embeds the query and searches ChromaDB for semantically similar chunks."""
    try:
        model = get_embedding_model()
        query_embedding = model.encode([query]).tolist()
        
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        if not results['documents'] or len(results['documents']) == 0 or len(results['documents'][0]) == 0:
            return json.dumps({"message": "No relevant protocols found in the database. Consider using ingest_emergency_document_url to add some."})
            
        retrieved_chunks = results['documents'][0]
        sources = [m.get("source", "Unknown") for m in results['metadatas'][0]]
        
        response = {
            "query": query,
            "results": [
                {"source": sources[i], "content": retrieved_chunks[i]} 
                for i in range(len(retrieved_chunks))
            ]
        }
        return json.dumps(response)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to query protocols: {str(e)}"})
