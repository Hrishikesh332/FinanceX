"""
KPI API - Fetches Key Performance Indicators from Cognee Knowledge Graph
"""
import os
import sys
import pathlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path to import cognee modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Set environment variables BEFORE importing cognee
os.environ["LLM_API_KEY"] = "."
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["LLM_MODEL"] = "cognee-distillabs-model-gguf-quantized"
os.environ["LLM_ENDPOINT"] = "http://localhost:11434/v1"
os.environ["LLM_MAX_TOKENS"] = "16384"

os.environ["EMBEDDING_PROVIDER"] = "ollama"
os.environ["EMBEDDING_MODEL"] = "nomic-embed-text:latest"
os.environ["EMBEDDING_ENDPOINT"] = "http://localhost:11434/api/embed"
os.environ["EMBEDDING_DIMENSIONS"] = "768"
os.environ["HUGGINGFACE_TOKENIZER"] = "nomic-ai/nomic-embed-text-v1.5"

from custom_retriever import GraphCompletionRetrieverWithUserPrompt

# Initialize FastAPI app
app = FastAPI(
    title="KPI API",
    description="API to fetch Key Performance Indicators from Cognee Knowledge Graph",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize retriever
system_prompt_path = pathlib.Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
retriever = None


def get_retriever():
    """Get or create the retriever instance."""
    global retriever
    if retriever is None:
        retriever = GraphCompletionRetrieverWithUserPrompt(
            user_prompt_filename="user_prompt.txt",
            system_prompt_path=str(system_prompt_path.resolve()),
            top_k=50,  # Increase to get more context for counting
        )
    return retriever


class KPIResponse(BaseModel):
    total_invoices: int
    total_transactions: int
    anomalies: int
    total_vendors: int


@app.on_event("startup")
async def startup_event():
    """Initialize the retriever on startup."""
    try:
        get_retriever()
        print("✓ KPI API initialized - Knowledge graph retriever ready")
    except Exception as e:
        print(f"✗ Failed to initialize retriever: {e}")


@app.get("/kpis", response_model=KPIResponse)
async def get_kpis():
    """
    Get KPIs from the knowledge graph.
    
    Returns:
        KPIResponse with counts from the knowledge graph
    """
    try:
        retriever_instance = get_retriever()
        
        # Query 1: Count total invoices
        invoices_query = "How many invoices are in the system? Give me just the number."
        invoices_response = await retriever_instance.get_completion(query=invoices_query)
        
        # Query 2: Count total transactions  
        transactions_query = "How many transactions are in the system? Give me just the number."
        transactions_response = await retriever_instance.get_completion(query=transactions_query)
        
        # Query 3: Detect anomalies
        anomalies_query = "How many payment discrepancies or mismatches are there? Give me just the number."
        anomalies_response = await retriever_instance.get_completion(query=anomalies_query)
        
        # Query 4: Count vendors
        vendors_query = "How many unique vendors are in the system? Give me just the number."
        vendors_response = await retriever_instance.get_completion(query=vendors_query)
        
        # Extract numbers from responses
        def extract_number(response_list):
            """Extract a number from the AI response."""
            if not response_list or len(response_list) == 0:
                return 0
            
            response = response_list[0].strip()
            
            # Try to extract numbers from the response
            import re
            numbers = re.findall(r'\d+', response)
            if numbers:
                return int(numbers[0])
            return 0
        
        total_invoices = extract_number(invoices_response)
        total_transactions = extract_number(transactions_response)
        anomalies = extract_number(anomalies_response)
        total_vendors = extract_number(vendors_response)
        
        return KPIResponse(
            total_invoices=total_invoices,
            total_transactions=total_transactions,
            anomalies=anomalies,
            total_vendors=total_vendors
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching KPIs: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "message": "KPI API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

