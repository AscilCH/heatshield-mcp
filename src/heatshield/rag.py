import os
import glob
import chromadb
import httpx
import pypdf
import io
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

async def ingest_document_from_url(url: str, filename: str) -> str:
    """
    Fetches a document (PDF or Text) from a URL, saves it, extracts text,
    and ingests it into the ChromaDB vector database dynamically.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            
        content = response.content
        
        # Ensure docs dir exists
        os.makedirs(DOCS_DIR, exist_ok=True)
        file_path = os.path.join(DOCS_DIR, filename)
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        text_content = ""
        
        # Extract text based on file extension
        if filename.lower().endswith(".pdf"):
            pdf_file = io.BytesIO(content)
            reader = pypdf.PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content += text + "\n\n"
        else:
            # Assume text/markdown
            text_content = content.decode("utf-8")
            
        if not text_content.strip():
            return f"Failed to extract any text from the downloaded file at {url}"
            
        # Chunk the text by paragraphs or large blocks
        paragraphs = [p.strip() for p in text_content.split("\n\n") if len(p.strip()) > 50]
        
        if not paragraphs:
            return "File downloaded, but no substantial paragraphs found to index."
            
        documents = []
        metadatas = []
        ids = []
        
        for chunk_id, para in enumerate(paragraphs):
            documents.append(para)
            metadatas.append({"source": filename, "chunk": chunk_id, "url": url})
            ids.append(f"{filename}_dynamic_{chunk_id}")
            
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return f"Successfully ingested {filename} from {url}. Indexed {len(paragraphs)} paragraphs into the RAG database."
        
    except Exception as e:
        return f"Error ingesting document from URL: {str(e)}"
