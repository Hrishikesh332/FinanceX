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
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import pandas as pd
import cognee
from custom_retriever import GraphCompletionRetrieverWithUserPrompt, CompletionResult
from cognee.api.v1.visualize.visualize import cognee_network_visualization

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
    sources: Optional[List[Dict[str, str]]] = None


class ChatWithSourcesResponse(BaseModel):
    """Response model for chat queries with source information"""
    answer: str
    session_id: Optional[str] = None
    sources: List[Dict[str, str]]
    graph_url: str


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
            "chat_with_sources": "/api/v1/chat/with-sources",
            "visualize_query": "/api/v1/visualize-query",
            "get_graph": "/api/v1/graphs/{filename}",
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


def triplets_to_graph_data(triplets) -> tuple:
    """
    Convert triplets/edges from a query result into graph data format 
    compatible with cognee_network_visualization.
    
    Returns:
        tuple: (nodes_data, edges_data) where:
            - nodes_data: list of (node_id, node_info) tuples
            - edges_data: list of (source, target, relation, edge_info) tuples
    """
    nodes_dict = {}  # Use dict to avoid duplicates
    edges_data = []
    
    for edge in triplets:
        try:
            source_node = edge.get_source_node() if hasattr(edge, 'get_source_node') else None
            target_node = edge.get_destination_node() if hasattr(edge, 'get_destination_node') else None
        except Exception:
            continue
        
        if source_node is None or target_node is None:
            continue
        
        # Extract source node info
        source_id = source_node.id if hasattr(source_node, 'id') else str(source_node)
        source_attrs = source_node.attributes if hasattr(source_node, 'attributes') else {}
        source_info = {
            "name": source_attrs.get('name', str(source_id)[:30]),
            "type": source_attrs.get('type', 'Entity'),
            "description": source_attrs.get('description', source_attrs.get('content', '')),
        }
        nodes_dict[source_id] = source_info
        
        # Extract target node info
        target_id = target_node.id if hasattr(target_node, 'id') else str(target_node)
        target_attrs = target_node.attributes if hasattr(target_node, 'attributes') else {}
        target_info = {
            "name": target_attrs.get('name', str(target_id)[:30]),
            "type": target_attrs.get('type', 'Entity'),
            "description": target_attrs.get('description', target_attrs.get('content', '')),
        }
        nodes_dict[target_id] = target_info
        
        # Extract edge info
        edge_attrs = edge.attributes if hasattr(edge, 'attributes') else {}
        relationship = edge_attrs.get('relationship_type', edge_attrs.get('relationship_name', 'related_to'))
        
        edges_data.append((
            source_id,
            target_id,
            relationship,
            edge_attrs
        ))
    
    # Convert nodes dict to list of tuples
    nodes_data = [(node_id, node_info) for node_id, node_info in nodes_dict.items()]
    
    return (nodes_data, edges_data)


def extract_sources_list(triplets) -> List[Dict[str, str]]:
    """Extract a list of source triplets in a readable format."""
    sources = []
    for edge in triplets:
        try:
            source_node = edge.get_source_node() if hasattr(edge, 'get_source_node') else None
            target_node = edge.get_destination_node() if hasattr(edge, 'get_destination_node') else None
        except Exception:
            continue
        
        if source_node is None or target_node is None:
            continue
        
        source_attrs = source_node.attributes if hasattr(source_node, 'attributes') else {}
        target_attrs = target_node.attributes if hasattr(target_node, 'attributes') else {}
        edge_attrs = edge.attributes if hasattr(edge, 'attributes') else {}
        
        sources.append({
            "source": source_attrs.get('name', str(source_node.id)[:30] if hasattr(source_node, 'id') else 'Unknown'),
            "relationship": edge_attrs.get('relationship_type', edge_attrs.get('relationship_name', 'related_to')),
            "target": target_attrs.get('name', str(target_node.id)[:30] if hasattr(target_node, 'id') else 'Unknown'),
        })
    
    return sources


@app.post("/api/v1/chat/with-sources", response_model=ChatWithSourcesResponse)
async def chat_with_sources(request: ChatRequest):
    """
    Query the knowledge graph and return the answer along with source references
    and a link to visualize the relevant subgraph.
    
    This endpoint returns:
    - **answer**: The response to the question
    - **sources**: List of knowledge graph triplets used to generate the answer
    - **graph_url**: URL to visualize the sources as an interactive graph
    
    - **query**: The question to ask
    - **session_id**: Optional session ID for conversation history
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Get retriever
        retriever = get_retriever()
        
        # Get completion WITH sources
        result: CompletionResult = await retriever.get_completion_with_sources(
            query=request.query.strip(),
            session_id=request.session_id
        )
        
        # Extract sources in readable format
        sources = extract_sources_list(result.triplets)
        
        # Generate a unique filename for this query's graph
        import hashlib
        query_hash = hashlib.md5(request.query.encode()).hexdigest()[:8]
        graph_filename = f"query_{query_hash}_sources.html"
        graph_path = Path(__file__).parent / "graphs" / graph_filename
        
        # Ensure graphs directory exists
        graph_path.parent.mkdir(exist_ok=True)
        
        # Generate graph visualization using cognee's visualization
        graph_data = triplets_to_graph_data(result.triplets)
        html_content = await cognee_network_visualization(graph_data, str(graph_path))
        
        return ChatWithSourcesResponse(
            answer=result.answer,
            session_id=request.session_id,
            sources=sources,
            graph_url=f"/api/v1/graphs/{graph_filename}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during chat: {str(e)}")


@app.get("/api/v1/graphs/{filename}", response_class=HTMLResponse)
async def get_graph_visualization(filename: str):
    """
    Serve the generated graph visualization HTML file.
    
    - **filename**: Name of the graph file to serve
    """
    try:
        graph_path = Path(__file__).parent / "graphs" / filename
        
        if not graph_path.exists():
            raise HTTPException(status_code=404, detail=f"Graph not found: {filename}")
        
        # Security check: ensure the file is within the graphs directory
        if not graph_path.resolve().is_relative_to((Path(__file__).parent / "graphs").resolve()):
            raise HTTPException(status_code=403, detail="Access denied")
        
        with open(graph_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving graph: {str(e)}")


@app.post("/api/v1/visualize-query")
async def visualize_query(request: ChatRequest):
    """
    Generate a graph visualization for a query without getting the full answer.
    Useful for exploring what information is available for a question.
    
    Returns the URL to the graph visualization and basic stats.
    
    - **query**: The question to visualize sources for
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Get retriever
        retriever = get_retriever()
        
        # Get just the context (triplets) without generating the full answer
        triplets = await retriever.get_context(request.query.strip())
        
        if not triplets:
            return {
                "message": "No relevant sources found for this query",
                "nodes_count": 0,
                "edges_count": 0,
                "graph_url": None
            }
        
        # Generate graph visualization
        import hashlib
        query_hash = hashlib.md5(request.query.encode()).hexdigest()[:8]
        graph_filename = f"explore_{query_hash}.html"
        graph_path = Path(__file__).parent / "graphs" / graph_filename
        graph_path.parent.mkdir(exist_ok=True)
        
        graph_data = triplets_to_graph_data(triplets)
        nodes_data, edges_data = graph_data
        
        await cognee_network_visualization(graph_data, str(graph_path))
        
        # Extract sources summary
        sources = extract_sources_list(triplets)
        
        return {
            "message": "Graph visualization generated",
            "query": request.query,
            "nodes_count": len(nodes_data),
            "edges_count": len(edges_data),
            "sources": sources,
            "graph_url": f"/api/v1/graphs/{graph_filename}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error visualizing query: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

