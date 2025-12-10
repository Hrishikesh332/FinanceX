"""
Graph API - Serves knowledge graph data for visualization
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables BEFORE importing cognee
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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from cognee.infrastructure.databases.graph import get_graph_engine

# Initialize FastAPI app
app = FastAPI(
    title="Graph API",
    description="API to serve knowledge graph data for visualization",
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


class GraphNode(BaseModel):
    id: str
    label: str
    type: str


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, int]


@app.get("/graph", response_model=GraphData)
async def get_graph_data():
    """
    Get knowledge graph data (nodes and edges) for visualization.
    
    Returns sample graph data representing invoices, transactions, and vendors.
    """
    try:
        # For now, return a representative sample of the graph structure
        # This represents the actual entities in the knowledge graph
        
        nodes = [
            # Vendors
            GraphNode(id="vendor_2", label="Vendor 2", type="vendor"),
            GraphNode(id="vendor_3", label="Vendor 3", type="vendor"),
            GraphNode(id="vendor_4", label="Vendor 4", type="vendor"),
            GraphNode(id="vendor_15", label="Vendor 15", type="vendor"),
            
            # Invoices
            GraphNode(id="inv_v2_m02", label="INV-V2-M02-828264", type="invoice"),
            GraphNode(id="inv_v3_m03", label="INV-V3-M03-200261", type="invoice"),
            GraphNode(id="inv_v4_m03", label="INV-V4-M03-326250", type="invoice"),
            GraphNode(id="inv_v15_m01", label="INV-V15-M01-282247", type="invoice"),
            
            # Transactions
            GraphNode(id="tx_v2_m02", label="TX-V2-M02-176206", type="transaction"),
            GraphNode(id="tx_v3_m03", label="TX-V3-M03-535592", type="transaction"),
            GraphNode(id="tx_v4_m03", label="TX-V4-M03-250998", type="transaction"),
            GraphNode(id="tx_v15_m01", label="TX-V15-M01-960858", type="transaction"),
            
            # Products
            GraphNode(id="prod_laptop", label="Lenovo ThinkPad X1", type="product"),
            GraphNode(id="prod_monitor", label="LG UltraWide Monitor", type="product"),
            GraphNode(id="prod_macbook", label="MacBook Pro 16\"", type="product"),
            GraphNode(id="prod_keyboard", label="HyperX Keyboard", type="product"),
        ]
        
        edges = [
            # Invoice to Vendor relationships
            GraphEdge(source="inv_v2_m02", target="vendor_2", relationship="issued_by"),
            GraphEdge(source="inv_v3_m03", target="vendor_3", relationship="issued_by"),
            GraphEdge(source="inv_v4_m03", target="vendor_4", relationship="issued_by"),
            GraphEdge(source="inv_v15_m01", target="vendor_15", relationship="issued_by"),
            
            # Transaction to Vendor relationships
            GraphEdge(source="tx_v2_m02", target="vendor_2", relationship="paid_to"),
            GraphEdge(source="tx_v3_m03", target="vendor_3", relationship="paid_to"),
            GraphEdge(source="tx_v4_m03", target="vendor_4", relationship="paid_to"),
            GraphEdge(source="tx_v15_m01", target="vendor_15", relationship="paid_to"),
            
            # Invoice to Product relationships
            GraphEdge(source="inv_v2_m02", target="prod_monitor", relationship="contains_item"),
            GraphEdge(source="inv_v3_m03", target="prod_laptop", relationship="contains_item"),
            GraphEdge(source="inv_v4_m03", target="prod_macbook", relationship="contains_item"),
            GraphEdge(source="inv_v15_m01", target="prod_keyboard", relationship="contains_item"),
            
            # Transaction to Invoice matching
            GraphEdge(source="tx_v2_m02", target="inv_v2_m02", relationship="matches"),
            GraphEdge(source="tx_v3_m03", target="inv_v3_m03", relationship="matches"),
            GraphEdge(source="tx_v4_m03", target="inv_v4_m03", relationship="matches"),
            GraphEdge(source="tx_v15_m01", target="inv_v15_m01", relationship="matches"),
        ]
        
        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "vendors": 4,
            "invoices": 4,
            "transactions": 4,
            "products": 4
        }
        
        return GraphData(nodes=nodes, edges=edges, stats=stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching graph data: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Graph API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

