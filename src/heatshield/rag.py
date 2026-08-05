import os
import glob
import chromadb
from chromadb.utils import embedding_functions

# Initialize ChromaDB client (local persistence)
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), ".chroma_db")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "emergency_docs")

client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Use default embedding function (sentence-transformers under the hood)
sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="emergency_protocols",
    embedding_function=sentence_transformer_ef
)

def _load_documents():
    """Reads all markdown files in the emergency_docs folder and adds them to Chroma."""
    # Check if we already loaded them (simple check)
    if collection.count() > 0:
        return
        
    doc_paths = glob.glob(os.path.join(DOCS_DIR, "*.md"))
    if not doc_paths:
        return
        
    documents = []
    metadatas = []
    ids = []
    
    for doc_id, doc_path in enumerate(doc_paths):
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
            filename = os.path.basename(doc_path)
            
            # Simple chunking by paragraph for better RAG retrieval
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            
            for chunk_id, para in enumerate(paragraphs):
                documents.append(para)
                metadatas.append({"source": filename, "chunk": chunk_id})
                ids.append(f"{filename}_{chunk_id}")
                
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

# Ensure docs are loaded on startup
_load_documents()

async def search_emergency_protocols(query: str, n_results: int = 3) -> str:
    """
    Semantic search over emergency protocols (WHO, CDC, local plans).
    Returns the most relevant text chunks and their source documents.
    """
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant emergency protocols found."
            
        formatted_results = ["# Retrieved Emergency Protocols\n"]
        
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            source = meta.get("source", "Unknown Document")
            formatted_results.append(f"**Source:** {source}\n{doc}\n")
            
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error querying vector database: {str(e)}"
