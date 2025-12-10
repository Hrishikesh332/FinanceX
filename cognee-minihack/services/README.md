# Services APIs

This directory contains FastAPI services that provide data to the Frontend application.

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| `data.py` | 8001 | Serves invoices and transactions from CSV files |
| `kpi.py` | 8002 | Fetches KPIs from Cognee knowledge graph |

## 1. Data API (`data.py`)

Serves raw invoice and transaction data from CSV files.

### Endpoints

#### GET /invoices
Returns all invoices from `optional_data_for_enrichment/new_invoices.csv`

**Response:**
```json
[
  {
    "invoice_number": "INV-V15-M01-282247",
    "date": "2025-02-23",
    "due_date": "2025-03-25",
    "vendor_id": 15,
    "total": 5108.92,
    "items": "[...]"
  }
]
```

#### GET /transactions
Returns all transactions from `optional_data_for_enrichment/new_transactions.csv`

**Response:**
```json
[
  {
    "transaction_id": "TX-V15-M01-960858",
    "date": "2025-02-07",
    "vendor_id": 15,
    "amount": 5108.92,
    "items": "[...]",
    "discount": 0.0
  }
]
```

### Running

```bash
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate
python services/data.py
```

API runs on: `http://localhost:8001`

## 2. KPI API (`kpi.py`)

Fetches Key Performance Indicators from the Cognee knowledge graph using AI-powered queries.

### Prerequisites

1. **Ollama** must be running with models:
   - `cognee-distillabs-model-gguf-quantized`
   - `nomic-embed-text:latest`

2. **Knowledge graph** must be loaded (run `python setup.py` first)

### Endpoints

#### GET /kpis
Queries the knowledge graph to get KPIs

**Response:**
```json
{
  "total_invoices": 9,
  "total_transactions": 8,
  "anomalies": 0,
  "total_vendors": 17
}
```

**How it works:**
1. Uses `GraphCompletionRetrieverWithUserPrompt` to query the knowledge graph
2. Asks specific questions like "How many invoices are in the system?"
3. Extracts numerical answers from AI responses
4. Returns structured KPI data

### Running

```bash
# Make sure Ollama is running first
ollama serve

# In another terminal:
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate
python services/kpi.py
```

API runs on: `http://localhost:8002`

## Running All Services

### Option 1: Multiple Terminals

**Terminal 1 - Data API:**
```bash
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate
python services/data.py
```

**Terminal 2 - KPI API:**
```bash
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate
python services/kpi.py
```

**Terminal 3 - Frontend:**
```bash
cd /Users/hrishikesh/Desktop/Finance/Frontend
npm run dev
```

### Option 2: Background Processes

```bash
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate

# Start Data API in background
python services/data.py > logs/data.log 2>&1 &
echo $! > data_api.pid

# Start KPI API in background
python services/kpi.py > logs/kpi.log 2>&1 &
echo $! > kpi_api.pid

# Start Frontend
cd ../Frontend
npm run dev
```

To stop:
```bash
kill $(cat data_api.pid)
kill $(cat kpi_api.pid)
```

## Testing

### Test Data API
```bash
curl http://localhost:8001/invoices | jq '.[0]'
curl http://localhost:8001/transactions | jq '.[0]'
```

### Test KPI API
```bash
curl http://localhost:8002/kpis | jq '.'
```

## Frontend Integration

The Frontend application expects these APIs to be running:

- **Dashboard**: Fetches from both `/kpis` (port 8002) and data APIs (port 8001)
- **Invoices Page**: Fetches from `/invoices` (port 8001)
- **Transactions Page**: Fetches from `/transactions` (port 8001)

## Troubleshooting

### KPI API returns 0 for all values

**Problem:** The knowledge graph queries aren't returning data

**Solutions:**
1. Verify Ollama is running: `ollama list`
2. Check if knowledge graph is loaded: `ls -la cognee_export/`
3. Re-import the graph: `python setup.py`
4. Check logs for specific error messages

### Data API returns 404

**Problem:** CSV files not found

**Solutions:**
1. Verify CSV files exist: `ls optional_data_for_enrichment/`
2. Check file permissions
3. Verify you're running from the correct directory

### CORS errors in Frontend

**Solution:** Both APIs have CORS enabled for all origins. If issues persist, check browser console for specific errors.

## Architecture

```
CSV Files → Data API (8001) → Frontend
    ↓
Knowledge Graph → KPI API (8002) → Frontend
    ↑
Ollama (LLM + Embeddings)
```
