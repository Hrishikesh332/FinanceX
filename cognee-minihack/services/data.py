"""
Simple FastAPI service for serving invoice and transaction data from CSV files.
"""
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="Data API",
    description="Simple API to serve invoices and transactions data",
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


@app.get("/invoices")
def get_invoices():
    """
    Get all invoices from the CSV file.
    
    Returns:
        List of invoice records
    """
    try:
        df = pd.read_csv(INVOICES_PATH)
        return df.to_dict(orient='records')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Invoices file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading invoices: {str(e)}")


@app.get("/transactions")
def get_transactions():
    """
    Get all transactions from the CSV file.
    
    Returns:
        List of transaction records
    """
    try:
        df = pd.read_csv(TRANSACTIONS_PATH)
        return df.to_dict(orient='records')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Transactions file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading transactions: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

