"""
Simple KPI API - Returns KPIs by directly counting CSV data
This is much faster than querying the knowledge graph with AI
"""
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Simple KPI API",
    description="Fast KPI metrics from CSV data",
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

# Data paths
BASE_DIR = Path(__file__).parent.parent
INVOICES_PATH = BASE_DIR / "optional_data_for_enrichment" / "new_invoices.csv"
TRANSACTIONS_PATH = BASE_DIR / "optional_data_for_enrichment" / "new_transactions.csv"


class KPIResponse(BaseModel):
    total_invoices: int
    total_transactions: int
    anomalies: int
    total_vendors: int


@app.get("/kpis", response_model=KPIResponse)
async def get_kpis():
    """
    Get KPIs from CSV data (fast version).
    
    Returns:
        KPIResponse with counts from CSV files
    """
    try:
        # Read CSV files
        invoices_df = pd.read_csv(INVOICES_PATH)
        transactions_df = pd.read_csv(TRANSACTIONS_PATH)
        
        # Calculate KPIs
        total_invoices = len(invoices_df)
        total_transactions = len(transactions_df)
        
        # Get unique vendors from both sources
        invoice_vendors = set(invoices_df['vendor_id'].unique())
        transaction_vendors = set(transactions_df['vendor_id'].unique())
        total_vendors = len(invoice_vendors.union(transaction_vendors))
        
        # Detect anomalies: transactions without matching invoices
        # or invoices without matching transactions
        invoice_set = set(invoices_df['vendor_id'].astype(str) + '-' + invoices_df['total'].astype(str))
        transaction_set = set(transactions_df['vendor_id'].astype(str) + '-' + transactions_df['amount'].astype(str))
        
        # Count mismatches as anomalies
        anomalies = len(invoice_set.symmetric_difference(transaction_set))
        
        return KPIResponse(
            total_invoices=total_invoices,
            total_transactions=total_transactions,
            anomalies=anomalies,
            total_vendors=total_vendors
        )
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="CSV files not found. Make sure new_invoices.csv and new_transactions.csv exist."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating KPIs: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Simple KPI API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

