"""
FinanceX Cognee FastAPI Application
====================================

This API provides endpoints for ingesting financial data and querying the knowledge graph.

Architecture:
-------------
1. **Ingestion Flow** (POST /api/v1/ingest/*):
   - Data → cognee.add() → cognee.cognify(custom_prompt) → Knowledge Graph
   - Uses prompts: invoice_prompt.txt or transaction_prompt.txt

2. **Chat/Query Flow** (POST /api/v1/chat):
   - Query → GraphCompletionRetrieverWithUserPrompt.get_completion()
     → generate_completion_with_user_prompt() (from custom_generate_completion.py)
     → LLMGateway.acreate_structured_output()
   - Uses prompts: system_prompt.txt (detailed instructions) + user_prompt.txt (template)

Key Components:
---------------
- custom_retriever.py: GraphCompletionRetrieverWithUserPrompt - retrieves context from graph
- custom_generate_completion.py: generate_completion_with_user_prompt() - formats prompts and calls LLM
- LLMGateway: cognee's LLM interface (configured for Ollama)
"""

import os
# Note: Environment variables must be set BEFORE importing cognee
# Since we are using Ollama locally, we do not need an API key, although it is important that it is defined, and not an empty string.
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

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import cognee
from custom_retriever import GraphCompletionRetrieverWithUserPrompt

app = FastAPI(
    title="FinanceX Cognee API",
    description="API for ingesting financial data and querying the knowledge graph",
    version="1.0.0"
)


def load_prompt(filename: str) -> str:
    """Load a prompt from the prompts directory"""
    prompt_path = Path(__file__).parent / "prompts" / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, 'r') as f:
        return f.read()


# Load prompts for ingestion (used with cognee.cognify)
INVOICE_PROMPT = load_prompt("invoice_prompt.txt")
TRANSACTION_PROMPT = load_prompt("transaction_prompt.txt")

# Prompt paths for chat/retrieval (used with custom_retriever and custom_generate_completion)
SYSTEM_PROMPT_PATH = str(Path(__file__).parent / "prompts" / "system_prompt.txt")
USER_PROMPT_FILENAME = "user_prompt.txt"

# Initialize retriever (lazy initialization)
# This retriever uses:
# - GraphCompletionRetrieverWithUserPrompt (from custom_retriever.py)
# - generate_completion_with_user_prompt (from custom_generate_completion.py)
# - LLMGateway.acreate_structured_output (from cognee)
_retriever: Optional[GraphCompletionRetrieverWithUserPrompt] = None


def get_retriever(
    user_prompt_filename: Optional[str] = None,
    system_prompt_path: Optional[str] = None,
    top_k: int = 10
) -> GraphCompletionRetrieverWithUserPrompt:
    """
    Get or create the retriever instance.
    
    The retriever uses the custom completion pipeline:
    1. GraphCompletionRetrieverWithUserPrompt retrieves context from the knowledge graph
    2. generate_completion_with_user_prompt (from custom_generate_completion.py) formats prompts
    3. LLMGateway.acreate_structured_output generates the final response
    
    Args:
        user_prompt_filename: Optional custom user prompt filename (default: "user_prompt.txt")
        system_prompt_path: Optional custom system prompt path
        top_k: Number of top results to retrieve (default: 10)
    
    Returns:
        GraphCompletionRetrieverWithUserPrompt instance
    """
    global _retriever
    if _retriever is None:
        _retriever = GraphCompletionRetrieverWithUserPrompt(
            user_prompt_filename=user_prompt_filename or USER_PROMPT_FILENAME,
            system_prompt_path=system_prompt_path or SYSTEM_PROMPT_PATH,
            top_k=top_k,
        )
    return _retriever


# Request/Response Models
class TextIngestionRequest(BaseModel):
    """Request model for text ingestion"""
    text: str
    data_type: str = "invoice"  # "invoice" or "transaction"
    custom_prompt: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for chat queries"""
    query: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat queries"""
    answer: str
    session_id: Optional[str] = None


class IngestionResponse(BaseModel):
    """Response model for ingestion"""
    message: str
    items_processed: int
    data_type: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FinanceX Cognee API",
        "version": "1.0.0",
        "endpoints": {
            "ingest_text": "/api/v1/ingest/text",
            "ingest_csv": "/api/v1/ingest/csv",
            "chat": "/api/v1/chat",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FinanceX Cognee API"}


@app.post("/api/v1/ingest/text", response_model=IngestionResponse)
async def ingest_text(request: TextIngestionRequest):
    """
    Ingest text data into the knowledge graph.
    
    - **text**: The text content to ingest
    - **data_type**: Type of data ("invoice" or "transaction")
    - **custom_prompt**: Optional custom prompt for processing
    """
    try:
        # Determine which prompt to use
        if request.custom_prompt:
            prompt = request.custom_prompt
        elif request.data_type.lower() == "invoice":
            prompt = INVOICE_PROMPT
        elif request.data_type.lower() == "transaction":
            prompt = TRANSACTION_PROMPT
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data_type: {request.data_type}. Must be 'invoice' or 'transaction'"
            )
        
        # Process the text
        # Split by lines or paragraphs if needed
        text_items = [line.strip() for line in request.text.split('\n') if line.strip()]
        
        if not text_items:
            raise HTTPException(status_code=400, detail="No text content provided")
        
        # Add data to cognee
        await cognee.add(text_items)
        
        # Create embeddings and build graph
        await cognee.cognify(custom_prompt=prompt)
        
        return IngestionResponse(
            message=f"Successfully ingested {len(text_items)} {request.data_type} items",
            items_processed=len(text_items),
            data_type=request.data_type
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during ingestion: {str(e)}")


@app.post("/api/v1/ingest/csv", response_model=IngestionResponse)
async def ingest_csv(
    file: UploadFile = File(...),
    data_type: str = Form("invoice"),
    delimiter: str = Form(","),
    max_rows: int = Form(10000)
):
    """
    Ingest CSV file data into the knowledge graph.
    
    - **file**: CSV file to upload
    - **data_type**: Type of data ("invoice" or "transaction")
    - **delimiter**: CSV delimiter (default: ",")
    - **max_rows**: Maximum number of rows to process (default: 10000)
    """
    try:
        # Validate data_type
        if data_type.lower() not in ["invoice", "transaction"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data_type: {data_type}. Must be 'invoice' or 'transaction'"
            )
        
        # Read CSV file
        contents = await file.read()
        
        # Determine delimiter based on data_type if not specified
        if data_type.lower() == "transaction" and delimiter == ",":
            delimiter = ";"  # Transactions typically use semicolon
        
        # Parse CSV
        import io
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')), sep=delimiter).head(max_rows)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty or could not be parsed")
        
        # Convert to list of strings (one per row)
        data_items = [str(row.to_dict()) for _, row in df.iterrows()]
        
        # Determine prompt
        if data_type.lower() == "invoice":
            prompt = INVOICE_PROMPT
        else:
            prompt = TRANSACTION_PROMPT
        
        # Add data to cognee
        await cognee.add(data_items)
        
        # Create embeddings and build graph
        await cognee.cognify(custom_prompt=prompt)
        
        return IngestionResponse(
            message=f"Successfully ingested {len(data_items)} {data_type} items from CSV",
            items_processed=len(data_items),
            data_type=data_type
        )
    
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during CSV ingestion: {str(e)}")


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Query the knowledge graph with a natural language question.
    
    This endpoint uses the custom completion pipeline:
    1. GraphCompletionRetrieverWithUserPrompt retrieves relevant context from the knowledge graph
    2. The context is formatted using the user_prompt.txt template (with {{ context }} and {{ question }} placeholders)
    3. generate_completion_with_user_prompt (from custom_generate_completion.py) handles:
       - Loading the system_prompt.txt
       - Combining conversation history if session_id is provided
       - Calling LLMGateway.acreate_structured_output for the final response
    
    - **query**: The question to ask
    - **session_id**: Optional session ID for conversation history (enables multi-turn conversations)
    
    The prompts used are:
    - System Prompt: prompts/system_prompt.txt (detailed instructions for financial analysis)
    - User Prompt: prompts/user_prompt.txt (template with context and question placeholders)
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Get retriever (uses GraphCompletionRetrieverWithUserPrompt)
        # This internally calls generate_completion_with_user_prompt from custom_generate_completion.py
        retriever = get_retriever()
        
        # Get completion
        # This triggers:
        # 1. Graph search to find relevant context
        # 2. User prompt rendering with context and question
        # 3. generate_completion_with_user_prompt() which uses LLMGateway.acreate_structured_output()
        results = await retriever.get_completion(
            query=request.query.strip(),
            session_id=request.session_id
        )
        
        if not results or len(results) == 0:
            raise HTTPException(status_code=500, detail="No response generated")
        
        answer = results[0] if isinstance(results, list) else str(results)
        
        return ChatResponse(
            answer=answer,
            session_id=request.session_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during chat: {str(e)}")


@app.get("/api/v1/stats")
async def get_stats():
    """Get statistics about the knowledge graph"""
    try:
        # This is a placeholder - you might want to add actual stats
        # For example, counting nodes/edges in the graph
        return {
            "message": "Statistics endpoint",
            "note": "Graph statistics can be added here"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

