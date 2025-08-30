import os
import json
import chromadb
from chromadb.utils import embedding_functions

# Use a common, lightweight sentence transformer model for embeddings
MODEL_NAME = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)

# Initialize ChromaDB client (persistent storage in './chroma_db')
client = chromadb.PersistentClient(path="./chroma_db")

# Get or create the collection for financial filings
COLLECTION_NAME = 'alpha_filings'
collection = client.get_or_create_collection(
    name=COLLECTION_NAME, 
    embedding_function=emb_fn
)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """Splits text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def ingest_filing(ticker: str, filing_path: str):
    """Chunks a filing and ingests it into ChromaDB."""
    print(f"Ingesting {filing_path} for ticker {ticker}...")
    with open(filing_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = chunk_text(content)
    ids = [f"{ticker}-{os.path.basename(filing_path)}-{i}" for i in range(len(chunks))]
    metadatas = [{'ticker': ticker, 'source': filing_path} for _ in chunks]
    
    collection.add(documents=chunks, metadatas=metadatas, ids=ids)
    print(f"Successfully ingested {len(chunks)} chunks.")
    return len(chunks)

# In rag/ingest_documents.py

def sample_ingest():
    """Ingests sample filings for all tickers in the back-test."""
    tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
    
    for ticker in tickers:
        os.makedirs('data/filings', exist_ok=True)
        demo_path = f'data/filings/{ticker}-10K-sample.txt'
        
        # Create a generic dummy file if it doesn't exist
        if not os.path.exists(demo_path):
            with open(demo_path, 'w') as f:
                f.write(f"This is a sample 10-K filing for {ticker}. The company is a leader in its respective market segment and faces competition. Financial performance has been stable.")
        
        ingest_filing(ticker, demo_path)

if __name__ == '__main__':
    sample_ingest()