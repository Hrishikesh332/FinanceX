"""
FinanceX Main Application Entry Point
======================================

This is the main entry point for running all FastAPI services.
It combines all services into a single application.

Usage:
    python app.py

Services included:
    - Data API (CSV data)
    - KPI API (Knowledge Graph metrics)
    - Main API (Chat & Ingestion)

All services are mounted under different paths:
    - /data/* - Data API endpoints
    - /kpi/* - KPI API endpoints
    - /api/* - Main API endpoints (chat, ingestion)
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the service apps
from services.data import app as data_app
from services.kpi_simple import app as kpi_app  # Using simple/fast KPI
from services.graph import app as graph_app
from services.api import app as main_api_app

# Create main application
app = FastAPI(
    title="FinanceX Complete API",
    description="Unified API for invoice reconciliation, data access, and KPI metrics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount sub-applications
app.mount("/data", data_app)
app.mount("/kpi", kpi_app)
app.mount("/graph", graph_app)
app.mount("/api", main_api_app)

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "message": "FinanceX API - Invoice Reconciliation System",
        "version": "1.0.0",
        "services": {
            "data": {
                "path": "/data",
                "description": "CSV data access (invoices & transactions)",
                "docs": "/data/docs"
            },
            "kpi": {
                "path": "/kpi",
                "description": "KPI metrics (fast CSV-based)",
                "docs": "/kpi/docs"
            },
            "graph": {
                "path": "/graph",
                "description": "Knowledge graph visualization data",
                "docs": "/graph/docs"
            },
            "main": {
                "path": "/api",
                "description": "Chat & data ingestion endpoints",
                "docs": "/api/docs"
            }
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health():
    """Health check for all services."""
    return {
        "status": "healthy",
        "services": {
            "data": "running",
            "kpi": "running",
            "main": "running"
        }
    }

if __name__ == "__main__":
    print("=" * 60)
    print("Starting FinanceX Complete API")
    print("=" * 60)
    print("\nServices available at:")
    print("  • Main API:    http://localhost:8000/api")
    print("  • Data API:    http://localhost:8000/data")
    print("  • KPI API:     http://localhost:8000/kpi")
    print("\nDocumentation:")
    print("  • Swagger UI:  http://localhost:8000/docs")
    print("  • ReDoc:       http://localhost:8000/redoc")
    print("\nEndpoints:")
    print("  • GET  /data/invoices      - Get all invoices")
    print("  • GET  /data/transactions  - Get all transactions")
    print("  • GET  /kpi/kpis          - Get KPI metrics")
    print("  • GET  /graph/graph       - Get graph visualization data")
    print("  • POST /api/v1/chat       - Chat with knowledge graph")
    print("  • POST /api/v1/ingest/*   - Ingest data")
    print("=" * 60)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

